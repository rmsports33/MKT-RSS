"""Authenticated factual approval bound to the exact persisted WP draft.

HMAC proves a trusted issuer signed the decision; it does NOT independently
prove that the article's claims are true. Keep the publish gate closed until
an independently reviewed evidence workflow and atomic WP transition exist.
"""
import hashlib
import hmac
import json
from datetime import datetime, timezone


def canonical_bytes(value):
    """Canonical UTF-8 JSON shared by issuer and verifier."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sign_factual_certificate(body, private_key, *, kid, protocol_version=1):
    """Ed25519 issuer helper: sign the complete M1 body, excluding `signature`."""
    if not isinstance(body, dict) or not hasattr(private_key, "sign"):
        raise ValueError("certificate_signing_key_invalid")
    if not isinstance(kid, str) or not kid.strip():
        raise ValueError("certificate_kid_missing")
    certificate = dict(body)
    certificate["protocol_version"] = protocol_version
    certificate["alg"] = "Ed25519"
    certificate["kid"] = kid
    certificate["signature"] = private_key.sign(
        canonical_bytes(certificate)).hex()
    return certificate


def draft_digest(post):
    if not isinstance(post, dict):
        return None
    if type(post.get("id")) is not int or post["id"] <= 0:
        return None
    if post.get("status") != "draft":
        return None
    categories = post.get("categories")
    if (not isinstance(categories, list) or
            any(type(i) is not int or i <= 0 for i in categories) or
            10 not in categories or 1 in categories):
        return None
    if type(post.get("featured_media")) is not int or post["featured_media"] <= 0:
        return None
    if not isinstance(post.get("slug"), str) or not post["slug"]:
        return None
    fields = {}
    for key in ("id", "status", "title", "content", "slug", "categories", "featured_media"):
        value = post.get(key)
        if key in ("title", "content") and isinstance(value, dict):
            value = value.get("raw") or value.get("rendered")
        if key == "categories":
            value = sorted(categories)
        if key in ("title", "content") and (not isinstance(value, str) or not value):
            return None
        fields[key] = value
    try:
        encoded = json.dumps(fields, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError):
        return None
    return hashlib.sha256(encoded).hexdigest()


def verify_factual_certificate(post, certificate, key, *, now=None):
    """Validate issuer identity, article binding, TTL and signature. Never writes.

    Ed25519 certificates declare `alg: Ed25519`; the verifier needs only the
    public key. Certificates without `alg` use the legacy HMAC path, restricted
    to trusted server-side verification. The two paths are never mixed.
    """
    if not isinstance(certificate, dict):
        return False
    alg = certificate.get("alg")
    if alg == "Ed25519":
        if not hasattr(key, "verify"):
            return False
        if (certificate.get("protocol_version") != 1
                or not isinstance(certificate.get("kid"), str)
                or not certificate["kid"].strip()):
            return False
    elif alg is not None:
        return False
    elif not isinstance(key, bytes) or len(key) < 32:
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
    expected_len = 128 if alg == "Ed25519" else 64
    if not isinstance(signature, str) or len(signature) != expected_len:
        return False
    body = {k: v for k, v in certificate.items() if k != "signature"}
    try:
        message = canonical_bytes(body)
        if alg == "Ed25519":
            key.verify(bytes.fromhex(signature), message)
            return True
        expected = hmac.new(key, message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)
    except Exception:
        return False
