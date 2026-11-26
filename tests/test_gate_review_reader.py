"""Read-only Gate V1 review reader tests. No real network calls."""
import pytest

from mkt_flow_p0.gate_review_reader import (
    ReviewReadBlocked, fetch_human_review, _validate_target,
)

SHA = "a" * 64
BASE = "https://conexotech.com.br"
USER = "svc"
PASS = "synthetic"
POST_ID = 9769


class Resp:
    def __init__(self, status, payload=None):
        self.status_code = status
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


class Session:
    def __init__(self, status=200, payload=None, raise_exc=False):
        self.status = status
        self.payload = payload if payload is not None else self.valid()
        self.raise_exc = raise_exc
        self.calls = []

    def valid(self):
        return {
            "post_id": POST_ID,
            "valid_for_current_version": True,
            "report": {
                "schema": "conexo-article-quality/1",
                "post_id": POST_ID,
                "snapshot_sha256": SHA,
                "fingerprint": "b" * 64,
                "veredito": "APTO_PARA_APROVACAO",
                "reviewer_id": 3,
                "reviewed_at": 1700000000,
                "review_mode": "independent",
                "checks": {
                    "titulo": {"estado": "VERIFICADO", "evidencia": ["trecho literal do artigo"]},
                    "fontes": {"estado": "VERIFICADO", "evidencia": ["https://example.org/fonte"]},
                },
            },
        }

    def get(self, url, **kw):
        self.calls.append((url, kw))
        if self.raise_exc:
            raise __import__("requests").RequestException("offline")
        return Resp(self.status, self.payload)


def fetch(session=None, **kw):
    params = dict(post_id=POST_ID, wp_url=BASE, wp_user=USER,
                  wp_app_password=PASS, session=session or Session())
    params.update(kw)
    return fetch_human_review(**params)


def test_valid_review_record_is_returned():
    out = fetch(Session())
    assert out["post_id"] == POST_ID
    assert out["snapshot_sha256"] == SHA
    assert out["reviewer_id"] == 3
    assert out["review_mode"] == "independent"
    assert out["source"] == "gate-v1-human-review"


def test_request_is_read_only_and_authenticated():
    s = Session()
    fetch(s)
    url, kw = s.calls[0]
    assert url == f"{BASE}/wp-json/conexo/v1/editorial/quality/{POST_ID}"
    assert kw["auth"] == (USER, PASS)
    assert kw["allow_redirects"] is False


def test_expected_sha_binding():
    assert fetch(Session(), expected_snapshot_sha256=SHA)["snapshot_sha256"] == SHA
    with pytest.raises(ReviewReadBlocked, match="SHA_MISMATCH"):
        fetch(Session(), expected_snapshot_sha256="c" * 64)


def test_unauthorized_is_blocked():
    with pytest.raises(ReviewReadBlocked, match="UNAUTHORIZED"):
        fetch(Session(status=401))


def test_forbidden_is_blocked():
    with pytest.raises(ReviewReadBlocked, match="FORBIDDEN"):
        fetch(Session(status=403))


def test_missing_report_is_blocked():
    with pytest.raises(ReviewReadBlocked, match="RECORD_MISSING"):
        fetch(Session(payload={"post_id": POST_ID, "valid_for_current_version": True}))


def test_stale_record_is_blocked():
    payload = Session().valid()
    payload["valid_for_current_version"] = False
    with pytest.raises(ReviewReadBlocked, match="STALE"):
        fetch(Session(payload=payload))


def test_not_approved_is_blocked():
    payload = Session().valid()
    payload["report"]["veredito"] = "BLOQUEADO"
    with pytest.raises(ReviewReadBlocked, match="NOT_APPROVED"):
        fetch(Session(payload=payload))


def test_invalid_schema_is_blocked():
    payload = Session().valid()
    payload["report"]["schema"] = "conexo-article-quality/2"
    with pytest.raises(ReviewReadBlocked, match="SCHEMA_INVALID"):
        fetch(Session(payload=payload))


def test_post_mismatch_is_blocked():
    payload = Session().valid()
    payload["post_id"] = 123
    with pytest.raises(ReviewReadBlocked, match="POST_MISMATCH"):
        fetch(Session(payload=payload))


def test_missing_reviewer_is_blocked():
    payload = Session().valid()
    payload["report"]["reviewer_id"] = 0
    with pytest.raises(ReviewReadBlocked, match="REVIEWER_INVALID"):
        fetch(Session(payload=payload))


def test_missing_evidence_is_blocked():
    payload = Session().valid()
    payload["report"]["checks"]["titulo"]["evidencia"] = []
    with pytest.raises(ReviewReadBlocked, match="EVIDENCE_MISSING"):
        fetch(Session(payload=payload))


def test_network_error_is_blocked():
    with pytest.raises(ReviewReadBlocked, match="OUTCOME_UNKNOWN"):
        fetch(Session(raise_exc=True))


def test_missing_credentials_is_blocked():
    with pytest.raises(ReviewReadBlocked, match="CREDENTIALS_MISSING"):
        fetch(Session(), wp_app_password="")


def test_validate_target_rejects_url_with_credentials():
    with pytest.raises(ReviewReadBlocked, match="WP_URL_INVALID"):
        _validate_target("https://user:pass@conexotech.com.br")


def test_validate_target_rejects_http():
    with pytest.raises(ReviewReadBlocked, match="NOT_HTTPS"):
        _validate_target("http://conexotech.com.br")


def test_validate_target_rejects_query_and_fragment():
    with pytest.raises(ReviewReadBlocked, match="WP_URL_INVALID"):
        _validate_target("https://conexotech.com.br/?x=1")
