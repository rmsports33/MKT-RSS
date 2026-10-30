import hashlib
import hmac
import json
from editorial_factual_certificate import draft_digest, verify_factual_certificate

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
