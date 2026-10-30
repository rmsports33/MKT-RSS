"""Authenticated factual approval bound to the exact persisted WP draft.

HMAC proves a trusted issuer signed the decision; it does NOT independently
prove that the article's claims are true. Keep the publish gate closed until
an independently reviewed evidence workflow and atomic WP transition exist.
"""
import hashlib
import hmac
import json
from datetime import datetime, timezone


def draft_digest(post):
    if not isinstance(post, dict):
        return None
    if type(post.get("id")) is not int or post["id"] <= 0:
        return None
    if post.get("status") != "draft":
        return None
    fields = {}
    for key in ("id", "status", "title", "content", "slug", "categories", "featured_media"):
        value = post.get(key)
        if key in ("title", "content") and isinstance(value, dict):
            value = value.get("raw") or value.get("rendered")
        fields[key] = value
    try:
        encoded = json.dumps(fields, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError):
        return None
    return hashlib.sha256(encoded).hexdigest()


def verify_factual_certificate(post, certificate, key, *, now=None):
    """Validate issuer identity, article binding, TTL and HMAC. Never writes."""
    if not isinstance(certificate, dict) or not isinstance(key, bytes) or len(key) < 32:
        return False
    digest = draft_digest(post)
    if not digest or certificate.get("draft_sha256") != digest:
        return False
    if certificate.get("decision") != "APROVADO":
        return False
    if certificate.get("version") != 1 or certificate.get("review_type") != "independent_human":
        return False
    if not isinstance(certificate.get("reviewer_id"), str) or not certificate["reviewer_id"].strip():
        return False
    if not isinstance(certificate.get("review_record_url"), str) or not certificate["review_record_url"].startswith("https://"):
        return False
    if not isinstance(certificate.get("evidence_refs"), list) or not certificate["evidence_refs"]:
        return False
    if not all(isinstance(x, str) and x.startswith("https://") for x in certificate["evidence_refs"]):
        return False
    if type(certificate.get("expires_at")) is not int or type(certificate.get("issued_at")) is not int:
        return False
    now = int(datetime.now(timezone.utc).timestamp()) if now is None else now
    if type(now) is not int or certificate["issued_at"] > now or now >= certificate["expires_at"]:
        return False
    if certificate["expires_at"] - certificate["issued_at"] > 86400:
        return False
    signature = certificate.get("signature")
    if not isinstance(signature, str) or len(signature) != 64:
        return False
    body = {k: v for k, v in certificate.items() if k != "signature"}
    try:
        message = json.dumps(body, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
        expected = hmac.new(key, message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)
    except (TypeError, ValueError):
        return False
