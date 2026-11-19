"""Fail-closed verification of a separately signed independent-review record.

The certificate HMAC authenticates the certificate issuer. The registry envelope
uses a DIFFERENT key and authenticates the fetched record returned by the lookup
adapter. The adapter is transport only; its data is never trusted without this
second signature. No network operation or publication is performed here.
"""
import hashlib
import hmac
import json

from editorial_factual_certificate import draft_digest, verify_factual_certificate
from editorial_review_registry import verify_registry_envelope


def _canonical_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sign_registry_record(record, registry_signing_key):
    """Test/issuer helper: produce the detached HMAC for a trusted registry record."""
    if not isinstance(record, dict) or not isinstance(registry_signing_key, bytes) or len(registry_signing_key) < 32:
        raise ValueError("trusted_registry_key_invalid")
    return hmac.new(registry_signing_key, _canonical_bytes(record), hashlib.sha256).hexdigest()


def verify_independent_review(post, certificate, signing_key, lookup_review,
                              registry_verification_key, *, now=None,
                              sequence_store=None):
    if not callable(lookup_review):
        return {"verified": False, "reason": "trusted_review_store_missing"}
    if not verify_factual_certificate(post, certificate, signing_key, now=now):
        return {"verified": False, "reason": "certificate_invalid"}
    try:
        envelope = lookup_review(certificate["review_record_url"])
    except Exception:
        return {"verified": False, "reason": "trusted_review_unavailable"}
    if not isinstance(envelope, dict):
        return {"verified": False, "reason": "review_record_missing"}

    alg = envelope.get("alg")
    if alg == "Ed25519":
        result = verify_registry_envelope(
            envelope, registry_verification_key, now=now,
            sequence_store=sequence_store)
        if not result["verified"]:
            return {"verified": False, "reason": result["reason"]}
        record = result["record"]
    elif alg is not None:
        return {"verified": False, "reason": "review_record_algorithm_unsupported"}
    else:
        # Legacy HMAC path: server-only key, retained for pre-Ed25519 fixtures.
        if (not isinstance(registry_verification_key, bytes)
                or len(registry_verification_key) < 32):
            return {"verified": False,
                    "reason": "trusted_registry_verification_key_missing"}
        record = envelope.get("record")
        signature = envelope.get("signature")
        if not isinstance(record, dict) or not isinstance(signature, str) or len(signature) != 64:
            return {"verified": False, "reason": "review_record_signature_missing"}
        try:
            expected_signature = hmac.new(
                registry_verification_key, _canonical_bytes(record), hashlib.sha256
            ).hexdigest()
        except (TypeError, ValueError):
            return {"verified": False, "reason": "review_record_invalid"}
        if not hmac.compare_digest(signature, expected_signature):
            return {"verified": False, "reason": "review_record_signature_invalid"}

    required = (
        record.get("reviewer_id") == certificate["reviewer_id"]
        and record.get("draft_sha256") == draft_digest(post)
        and record.get("decision") == "APROVADO"
        and record.get("status") == "FINAL"
        and record.get("independent") is True
        and record.get("evidence_refs") == certificate["evidence_refs"]
        and record.get("review_record_url") == certificate["review_record_url"]
        and record.get("revoked") is False
    )
    if not required:
        return {"verified": False, "reason": "review_record_mismatch"}
    return {"verified": True, "reason": None}
