import hashlib
import hmac
import json
import pytest
from editorial_factual_certificate import (
    draft_digest, issue_factual_certificate, verify_factual_certificate,
)

POST = {"id": 41, "title": "Notícia", "content": "<p>Texto</p>",
        "slug": "noticia", "categories": [10], "featured_media": 12, "status": "draft"}
KEY = b"independent-review-backend-key-32bytes-12345"

def signed(post=POST, **changes):
    cert = {"draft_sha256": draft_digest(post), "reviewer_id": "human-reviewer",
            "evidence_refs": ["https://example.org/source"], "decision": "APROVADO",
            "issued_at": 100, "expires_at": 200, "version": 1,
            "review_type": "independent_human",
            "review_record_url": "https://example.org/review-record", **changes}
    message = json.dumps(cert, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode()
    cert["signature"] = hmac.new(KEY, message, hashlib.sha256).hexdigest()
    return cert

def review_record(**changes):
    return {"reviewer_id": "human-reviewer",
            "evidence_refs": ["https://example.org/source"],
            "decision": "APROVADO", "review_type": "independent_human",
            "review_record_url": "https://example.org/review-record", **changes}

def test_php_python_golden_digest():
    assert draft_digest(POST) == "1341bb92c336ebacfca6f3bd0284b3ff6744eab27519b072ef1b2ef9fa26becc"

def test_valid_signature_and_binding():
    assert verify_factual_certificate(POST, signed(), KEY, now=150)

def test_modified_article_rejected():
    assert not verify_factual_certificate({**POST, "content": "alterado"}, signed(), KEY, now=150)

def test_expired_rejected():
    assert not verify_factual_certificate(POST, signed(), KEY, now=200)

def test_forged_signature_rejected():
    assert not verify_factual_certificate(POST, {**signed(), "signature": "0"*64}, KEY, now=150)

def test_missing_evidence_rejected():
    assert not verify_factual_certificate(POST, signed(evidence_refs=[]), KEY, now=150)

def test_short_key_rejected():
    assert not verify_factual_certificate(POST, signed(), b"weak", now=150)

def test_future_issued_rejected():
    assert not verify_factual_certificate(POST, signed(), KEY, now=99)

def test_status_change_invalidates_certificate():
    assert not verify_factual_certificate({**POST, "status": "publish"}, signed(), KEY, now=150)

def test_missing_review_record_blocks():
    assert not verify_factual_certificate(POST, signed(review_record_url=""), KEY, now=150)

def test_wrong_review_type_blocks():
    assert not verify_factual_certificate(POST, signed(review_type="automatic"), KEY, now=150)

def test_issuer_creates_verifiable_certificate_bound_to_draft():
    certificate = issue_factual_certificate(POST, review_record(), KEY, now=100, ttl_seconds=3600)
    assert certificate["draft_sha256"] == draft_digest(POST)
    assert certificate["issued_at"] == 100
    assert certificate["expires_at"] == 3700
    assert verify_factual_certificate(POST, certificate, KEY, now=101)

def test_issuer_rejects_non_draft_or_incomplete_post():
    with pytest.raises(ValueError, match="draft_not_signable"):
        issue_factual_certificate({**POST, "status": "publish"}, review_record(), KEY, now=100)

def test_issuer_requires_independent_human_decision():
    with pytest.raises(ValueError, match="independent_human"):
        issue_factual_certificate(POST, review_record(review_type="automatic"), KEY, now=100)
    with pytest.raises(ValueError, match="independent_human"):
        issue_factual_certificate(POST, review_record(decision="REPROVADO"), KEY, now=100)

def test_issuer_rejects_missing_evidence_and_invalid_record_url():
    with pytest.raises(ValueError, match="evidence_refs_invalid"):
        issue_factual_certificate(POST, review_record(evidence_refs=[]), KEY, now=100)
    with pytest.raises(ValueError, match="review_record_url_invalid"):
        issue_factual_certificate(POST, review_record(review_record_url="http://example.org/review"), KEY, now=100)

def test_issuer_rejects_weak_key_and_excessive_ttl():
    with pytest.raises(ValueError, match="signing_key_invalid"):
        issue_factual_certificate(POST, review_record(), b"weak", now=100)
    with pytest.raises(ValueError, match="ttl_invalid"):
        issue_factual_certificate(POST, review_record(), KEY, now=100, ttl_seconds=86401)

def test_issuer_rejects_duplicate_evidence_refs():
    with pytest.raises(ValueError, match="duplicate_evidence_ref"):
        issue_factual_certificate(POST, review_record(
            evidence_refs=["https://example.org/source", "https://example.org/source"]),
            KEY, now=100)
