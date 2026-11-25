"""Steps 4/5 integration tests. No network, no WordPress writes."""
import hashlib
import hmac
import json
import pytest

from editorial_factual_certificate import draft_digest
from mkt_flow_p0 import gate_certified_publish as gcp
from mkt_flow_p0.gate_review_reader import fetch_human_review
from mkt_flow_p0.wp_destination import CANONICAL_SITE

KEY = b"independent-review-backend-key-32bytes-12345"
POST = {"id": 41, "title": "Notícia", "content": "<p>Texto</p>",
        "slug": "noticia", "categories": [10], "featured_media": 12, "status": "draft"}
OP = "operation-id-unique-0001"
SHA = draft_digest(POST)
ENV = {"WP_OPERATION_MODE": "production", "GITHUB_ENVIRONMENT": "",
       "WP_URL": CANONICAL_SITE, "WP_USER": "svc", "WP_APP_PASSWORD": "pw"}


def cert():
    data = {"draft_sha256": SHA, "reviewer_id": "human-reviewer",
            "evidence_refs": ["https://example.org/source"], "decision": "APROVADO",
            "issued_at": 100, "expires_at": 200, "version": 1,
            "review_type": "independent_human",
            "review_record_url": "https://example.org/review-record"}
    body = json.dumps(data, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode()
    return {**data, "signature": hmac.new(KEY, body, hashlib.sha256).hexdigest()}


def cas(committed=None):
    state = {"calls": 0}
    def backend(post_id, digest, operation_id, certificate):
        state["calls"] += 1
        if committed is True:
            return {"committed": True, "post_id": post_id, "status": "publish"}
        return {"committed": False, "post_id": post_id, "status": "draft"}
    return backend, state


def test_certified_publish_requires_certificate():
    backend, state = cas(True)
    with pytest.raises(gcp.CertifiedPublishBlocked):
        gcp.certified_publish(POST, {}, KEY, OP, backend, now=150, env=ENV)
    assert state["calls"] == 0


def test_certified_publish_requires_destination():
    backend, state = cas(True)
    with pytest.raises(gcp.CertifiedPublishBlocked):
        gcp.certified_publish(POST, cert(), KEY, OP, backend, now=150,
                              env={**ENV, "WP_OPERATION_MODE": ""})
    assert state["calls"] == 0


def test_certified_publish_blocked_in_validation():
    backend, state = cas(True)
    with pytest.raises(gcp.CertifiedPublishBlocked, match="VALIDATION"):
        gcp.certified_publish(POST, cert(), KEY, OP, backend, now=150,
                              env={**ENV, "GITHUB_ENVIRONMENT": "rss-homolog"})
    assert state["calls"] == 0


def test_certified_publish_requires_cas_confirmation():
    backend, state = cas(False)
    out = gcp.certified_publish(POST, cert(), KEY, OP, backend, now=150, env=ENV)
    assert out["published"] is False
    assert state["calls"] == 1


def test_certified_publish_succeeds_with_cas():
    backend, state = cas(True)
    out = gcp.certified_publish(POST, cert(), KEY, OP, backend, now=150, env=ENV)
    assert out["published"] is True
    assert out["operation_id"] == OP


def test_certificate_issued_from_authenticated_gate_review():
    review = {
        "post_id": 41, "snapshot_sha256": SHA, "reviewer_id": 3,
        "reviewed_at": 150, "review_mode": "independent",
        "checks": {"titulo": {"estado": "VERIFICADO",
                              "evidencia": ["https://example.org/a"]}},
        "review_record_url": "https://conexotech.com.br/wp-json/conexo/v1/editorial/quality/41",
    }
    # A valid authenticated review issues a verifiable certificate.
    _, certificate = gcp.build_certificate_from_gate(
        POST, wp_url=CANONICAL_SITE, wp_user="svc", wp_app_password="pw",
        signing_key=KEY, session=_FakeSession(review))
    assert certificate["draft_sha256"] == SHA
    assert certificate["reviewer_id"] == "3"


def test_gate_cas_backend_uses_real_route_and_reports_commit():
    class CasSession:
        def __init__(self):
            self.posts = []
        def post(self, url, **kw):
            self.posts.append((url, kw))
            class R:
                status_code = 200
                @staticmethod
                def json():
                    return {"committed": True, "post_id": 41, "status": "publish"}
            return R()
    s = CasSession()
    backend = gcp.gate_cas_backend(wp_url=CANONICAL_SITE, wp_user="svc",
                                   wp_app_password="pw", session=s)
    result = gcp.certified_publish(POST, cert(), KEY, OP, backend, now=150, env=ENV)
    assert result["published"] is True
    url, kw = s.posts[0]
    assert url == f"{CANONICAL_SITE}/wp-json/conexo/v1/editorial/atomic-commit"
    assert kw["json"]["operation_id"] == OP
    assert kw["json"]["expected_sha256"] == SHA


def test_gate_cas_backend_fails_closed_on_rejection():
    class RejectSession:
        def post(self, url, **kw):
            class R:
                status_code = 403
                @staticmethod
                def json():
                    return {}
            return R()
    backend = gcp.gate_cas_backend(wp_url=CANONICAL_SITE, wp_user="svc",
                                   wp_app_password="pw", session=RejectSession())
    result = gcp.certified_publish(POST, cert(), KEY, OP, backend, now=150, env=ENV)
    assert result["published"] is False


class _FakeSession:
    def __init__(self, review):
        self.review = review

    def get(self, url, **kw):
        checks = self.review["checks"]
        class R:
            status_code = 200
            @staticmethod
            def json():
                return {"post_id": 41, "valid_for_current_version": True,
                        "report": {"schema": "conexo-article-quality/1",
                                   "post_id": 41, "snapshot_sha256": SHA,
                                   "veredito": "APTO_PARA_APROVACAO",
                                   "reviewer_id": 3, "reviewed_at": 150,
                                   "review_mode": "independent",
                                   "checks": checks}}
        return R()
