"""Authenticated factual approval bound to the exact persisted WP draft.

HMAC proves a trusted issuer signed the decision; it does NOT independently
prove that the article's claims are true. Keep the publish gate closed until
an independently reviewed evidence workflow and atomic WP transition exist.

The issuer below is a signing primitive, not an identity provider. Its caller
MUST obtain review_record from an authenticated independent-human workflow.
This module does not authenticate a reviewer, fetch evidence, or publish.
"""
import hashlib
import hmac
import json
from datetime import datetime, timezone
from urllib.parse import urlsplit


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


def _certificate_message(body):
    return json.dumps(body, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _is_https_reference(value):
    if not isinstance(value, str) or len(value) > 2048:
        return False
    try:
        parsed = urlsplit(value)
        return (parsed.scheme == "https" and bool(parsed.hostname)
                and not parsed.username and not parsed.password)
    except ValueError:
        return False


def issue_factual_certificate(post, review_record, key, *, now=None, ttl_seconds=86400):
    """Sign a factual review record for one exact persisted draft.

    Trust boundary: review_record must come from an authenticated,
    independent-human review service. This function validates its shape but
    cannot establish reviewer identity or independently verify evidence.

    The key must remain in the trusted issuer environment and must never be
    included in a package, certificate, repository, or client response.
    """
    if not isinstance(key, bytes) or len(key) < 32:
        raise ValueError("factual_certificate_signing_key_invalid")
    digest = draft_digest(post)
    if not digest:
        raise ValueError("factual_certificate_draft_not_signable")
    if not isinstance(review_record, dict):
        raise ValueError("factual_certificate_review_record_invalid")

    reviewer_id = review_record.get("reviewer_id")
    record_url = review_record.get("review_record_url")
    evidence_refs = review_record.get("evidence_refs")
    if (review_record.get("decision") != "APROVADO"
            or review_record.get("review_type") != "independent_human"):
        raise ValueError("factual_certificate_independent_human_approval_required")
    if (not isinstance(reviewer_id, str) or not reviewer_id.strip()
            or len(reviewer_id.strip()) > 120):
        raise ValueError("factual_certificate_reviewer_invalid")
    if not _is_https_reference(record_url):
        raise ValueError("factual_certificate_review_record_url_invalid")
    if (not isinstance(evidence_refs, list) or not 1 <= len(evidence_refs) <= 50
            or not all(_is_https_reference(item) for item in evidence_refs)):
        raise ValueError("factual_certificate_evidence_refs_invalid")
    if len(set(evidence_refs)) != len(evidence_refs):
        raise ValueError("factual_certificate_duplicate_evidence_ref")

    issued_at = int(datetime.now(timezone.utc).timestamp()) if now is None else now
    if type(issued_at) is not int:
        raise ValueError("factual_certificate_issued_at_invalid")
    if type(ttl_seconds) is not int or not 1 <= ttl_seconds <= 86400:
        raise ValueError("factual_certificate_ttl_invalid")

    body = {
        "draft_sha256": digest,
        "reviewer_id": reviewer_id.strip(),
        "evidence_refs": list(evidence_refs),
        "decision": "APROVADO",
        "issued_at": issued_at,
        "expires_at": issued_at + ttl_seconds,
        "version": 1,
        "review_type": "independent_human",
        "review_record_url": record_url,
    }
    signature = hmac.new(key, _certificate_message(body), hashlib.sha256).hexdigest()
    return {**body, "signature": signature}


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
    if not _is_https_reference(certificate.get("review_record_url")):
        return False
    if not isinstance(certificate.get("evidence_refs"), list) or not certificate["evidence_refs"]:
        return False
    if not all(_is_https_reference(x) for x in certificate["evidence_refs"]):
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
        expected = hmac.new(key, _certificate_message(body), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)
    except (TypeError, ValueError):
        return False
