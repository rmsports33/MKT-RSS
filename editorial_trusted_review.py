"""Fail-closed human review attestation, distinct from signature verification.

A certificate signature authenticates the issuer, not the existence of an
independent editorial review. A trusted review store must be queried separately.
This function performs no network operation of its own.
"""
from editorial_factual_certificate import draft_digest, verify_factual_certificate


def verify_independent_review(post, certificate, signing_key, lookup_review, *,
                              now=None):
    if not callable(lookup_review):
        return {"verified": False, "reason": "trusted_review_store_missing"}
    if not verify_factual_certificate(post, certificate, signing_key, now=now):
        return {"verified": False, "reason": "certificate_invalid"}
    try:
        record = lookup_review(certificate["review_record_url"])
    except Exception:
        return {"verified": False, "reason": "trusted_review_unavailable"}
    if not isinstance(record, dict):
        return {"verified": False, "reason": "review_record_missing"}
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
