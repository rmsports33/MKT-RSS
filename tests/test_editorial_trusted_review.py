import hashlib
import hmac
import json

import pytest

from editorial_factual_certificate import draft_digest
from editorial_trusted_review import sign_registry_record, verify_independent_review

KEY = b"test-only-certificate-key-32-bytes-minimum"
REGISTRY_KEY = b"test-only-registry-key-32-bytes-minimum"
POST = {"id": 42, "status": "draft", "title": "Noticia", "content": "<p>Texto</p>",
        "slug": "noticia", "categories": [10], "featured_media": 12}


def fixture():
    cert = {"version": 1, "review_type": "independent_human",
            "draft_sha256": draft_digest(POST), "decision": "APROVADO",
            "reviewer_id": "reviewer-42", "review_record_url": "https://example.org/reviews/42",
            "evidence_refs": ["https://example.org/source"],
            "issued_at": 100, "expires_at": 200}
    payload = json.dumps(cert, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode()
    cert["signature"] = hmac.new(KEY, payload, hashlib.sha256).hexdigest()
    record = {"reviewer_id": "reviewer-42", "review_record_url": cert["review_record_url"],
              "draft_sha256": draft_digest(POST), "decision": "APROVADO", "status": "FINAL",
              "independent": True, "revoked": False, "evidence_refs": cert["evidence_refs"]}
    return cert, record


def envelope(record):
    return {"record": record, "signature": sign_registry_record(record, REGISTRY_KEY)}


def verify(cert, lookup, *, registry_key=REGISTRY_KEY, now=150):
    return verify_independent_review(POST, cert, KEY, lookup, registry_key, now=now)


def test_valid_signed_registry_record_passes():
    cert, record = fixture()
    assert verify(cert, lambda _: envelope(record))["verified"] is True


def test_self_asserted_verified_flag_is_not_a_registry_envelope():
    cert, _ = fixture()
    assert not verify(cert, lambda _: {"verified": True})["verified"]


def test_unsigned_record_is_rejected():
    cert, record = fixture()
    assert verify(cert, lambda _: {"record": record})["reason"] == "review_record_signature_missing"


def test_forged_or_tampered_registry_signature_is_rejected():
    cert, record = fixture()
    signed = envelope(record)
    tampered = {**record, "decision": "REJEITADO"}
    assert verify(cert, lambda _: {"record": tampered, "signature": signed["signature"]})["reason"] == "review_record_signature_invalid"


def test_missing_registry_verification_key_is_rejected():
    cert, record = fixture()
    assert verify(cert, lambda _: envelope(record), registry_key=None)["verified"] is False


@pytest.mark.parametrize(("field", "value"), [
    ("decision", "REJEITADO"), ("status", "PENDING"), ("independent", False),
    ("revoked", True), ("reviewer_id", "other"), ("draft_sha256", "0" * 64),
    ("evidence_refs", []), ("review_record_url", "https://example.org/other"),
])
def test_signed_but_mismatched_record_is_rejected(field, value):
    cert, record = fixture()
    record[field] = value
    assert verify(cert, lambda _: envelope(record))["reason"] == "review_record_mismatch"


def test_missing_record_is_rejected():
    cert, _ = fixture()
    assert verify(cert, lambda _: None)["reason"] == "review_record_missing"


def test_lookup_exception_and_timeout_fail_closed():
    cert, _ = fixture()
    def fail(_):
        raise TimeoutError("store down")
    assert verify(cert, fail)["reason"] == "trusted_review_unavailable"


def test_expired_certificate_is_rejected():
    cert, record = fixture()
    assert verify(cert, lambda _: envelope(record), now=201)["reason"] == "certificate_invalid"


def test_changed_article_denied_before_lookup():
    cert, record = fixture()
    changed = {**POST, "content": "changed"}
    called = []
    result = verify_independent_review(changed, cert, KEY,
        lambda _: called.append(True) or envelope(record), REGISTRY_KEY, now=150)
    assert result["verified"] is False
    assert called == []


def test_certificate_signature_invalid_is_rejected():
    cert, record = fixture()
    cert["signature"] = "0" * 64
    assert verify(cert, lambda _: envelope(record))["reason"] == "certificate_invalid"
