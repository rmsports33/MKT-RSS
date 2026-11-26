"""Testes do registro confiável com envelope assinado (PR #129, atualizado)."""
import hashlib
import hmac
import json

from editorial_factual_certificate import draft_digest
from editorial_trusted_review import verify_independent_review

KEY = b"test-only-secret-key-with-adequate-length-123"
REGISTRY_KEY = b"test-only-registry-key-with-adequate-length-456"
POST = {"id": 42, "status": "draft", "title": "Noticia", "content": "<p>Texto</p>",
        "slug": "noticia", "categories": [10], "featured_media": 12}


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def fixture():
    cert = {"version": 1, "review_type": "independent_human",
            "draft_sha256": draft_digest(POST), "decision": "APROVADO",
            "reviewer_id": "reviewer-42", "review_record_url": "https://example.org/reviews/42",
            "evidence_refs": ["https://example.org/source"],
            "issued_at": 100, "expires_at": 200}
    cert["signature"] = hmac.new(KEY, _canonical(cert), hashlib.sha256).hexdigest()
    record = {"reviewer_id": "reviewer-42", "review_record_url": cert["review_record_url"],
              "draft_sha256": draft_digest(POST), "decision": "APROVADO", "status": "FINAL",
              "independent": True, "revoked": False, "evidence_refs": cert["evidence_refs"]}
    return cert, record


def envelope(record, key=REGISTRY_KEY):
    return {"record": record,
            "signature": hmac.new(key, _canonical(record), hashlib.sha256).hexdigest()}


def test_matching_verified_record():
    cert, record = fixture()
    assert verify_independent_review(POST, cert, KEY, lambda _: envelope(record),
                                     REGISTRY_KEY, now=150)["verified"]


def test_no_review_store_is_denied():
    cert, _ = fixture()
    assert not verify_independent_review(POST, cert, KEY, None, REGISTRY_KEY, now=150)["verified"]


def test_revoked_approval_denied():
    cert, record = fixture()
    assert not verify_independent_review(
        POST, cert, KEY, lambda _: envelope({**record, "revoked": True}),
        REGISTRY_KEY, now=150)["verified"]


def test_changed_article_denied_before_lookup():
    cert, record = fixture()
    assert not verify_independent_review(
        {**POST, "content": "changed"}, cert, KEY,
        lambda _: envelope(record), REGISTRY_KEY, now=150)["verified"]


def test_mismatched_reviewer_denied():
    cert, record = fixture()
    assert not verify_independent_review(
        POST, cert, KEY, lambda _: envelope({**record, "reviewer_id": "other"}),
        REGISTRY_KEY, now=150)["verified"]


def test_store_error_denied():
    cert, _ = fixture()
    def fail(_):
        raise TimeoutError("store down")
    assert not verify_independent_review(POST, cert, KEY, fail, REGISTRY_KEY, now=150)["verified"]


def test_unsigned_envelope_denied():
    cert, record = fixture()
    assert not verify_independent_review(
        POST, cert, KEY, lambda _: {"record": record}, REGISTRY_KEY, now=150)["verified"]


def test_tampered_record_denied():
    cert, record = fixture()
    assert not verify_independent_review(
        POST, cert, KEY, lambda _: {**envelope(record), "record": {**record, "decision": "REPROVADO"}},
        REGISTRY_KEY, now=150)["verified"]
