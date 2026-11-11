"""Offline integrity and evidence-status audit for the one-shot Groq handoff.

No key, network, API, WordPress, Groq request or unpublished plaintext is used.
An intact encrypted artifact is NOT a factual or editorial approval.
"""
import argparse
import base64
import hashlib
import json
import zipfile
from pathlib import Path


class EvidenceAuditError(ValueError):
    pass


def audit_artifact(archive):
    archive = Path(archive)
    if archive.stat().st_size > 16 * 1024 * 1024:
        raise EvidenceAuditError("ARTIFACT_TOO_LARGE")
    try:
        with zipfile.ZipFile(archive) as z:
            if set(z.namelist()) != {"manifest.json", "handoff-encrypted.json"}:
                raise EvidenceAuditError("UNEXPECTED_ARCHIVE_MEMBERS")
            if any(i.file_size > 32 * 1024 * 1024 for i in z.infolist()):
                raise EvidenceAuditError("UNEXPECTED_MEMBER_SIZE")
            manifest = json.loads(z.read("manifest.json"))
            sealed = json.loads(z.read("handoff-encrypted.json"))
        if sealed.get("schema") != "mkt-handoff-live/1":
            raise EvidenceAuditError("INVALID_SEALED_SCHEMA")
        ciphertext = base64.b64decode(sealed["ciphertext"], validate=True)
        for key in ("nonce", "wrapped_key"):
            if not base64.b64decode(sealed[key], validate=True):
                raise EvidenceAuditError("MISSING_CRYPTO_MATERIAL")
        if hashlib.sha256(ciphertext).hexdigest() != sealed["ciphertext_sha256"]:
            raise EvidenceAuditError("CIPHERTEXT_HASH_MISMATCH")
        if manifest.get("schema") != "mkt-live-handoff-receipt/1":
            raise EvidenceAuditError("INVALID_RECEIPT_SCHEMA")
    except EvidenceAuditError:
        raise
    except (OSError, ValueError, TypeError, KeyError, zipfile.BadZipFile):
        raise EvidenceAuditError("INVALID_ARTIFACT") from None
    pending = manifest.get("quality_pending")
    if not isinstance(pending, list):
        pending = []
    handoff_created = (
        manifest.get("outcome") in {"HANDOFF_CREATED", "HANDOFF_CREATED_QUALITY_PENDING"}
        and manifest.get("process_exit_code") == 0
        and manifest.get("expected_results") == 1
        and manifest.get("wordpress_written") is False
    )
    review_validity_claimed = bool(
        manifest.get("review_method") in {"assisted", "human"}
        and isinstance(manifest.get("substantive_scores"), dict)
        and set(manifest["substantive_scores"]) ==
            {"reader_need", "editorial_angle", "decision_support", "voice", "source_limits"}
        and all(type(v) is int and v >= 3 for v in manifest["substantive_scores"].values())
    )
    complete_claim = manifest.get("quality_status") == "PRONTO_PARA_REVISAO_HUMANA"
    return {
        "schema": "mkt-live-handoff-offline-audit/1",
        "archive_integrity": "PASS",
        "encrypted_evidence_present": True,
        "plaintext_decrypted": False,
        "technical_handoff_created": handoff_created,
        "editorial_readiness_claim": "READY_FOR_HUMAN_REVIEW" if
            complete_claim and review_validity_claimed and not pending else "PENDING",
        "substantive_review_receipt": "PRESENT_CLAIM_UNVERIFIED" if
            review_validity_claimed else "ABSENT_OR_INVALID",
        "quality_pending": sorted(set(x for x in pending if isinstance(x, str))),
        "review_diagnostics": [
            x for x in manifest.get("review_diagnostics", [])
            if isinstance(x, str) and x in {
                "NOT_RUN_NO_BRIEF", "NOT_RUN_NO_VALID_HANDOFF",
                "HANDOFF_INVALID", "PROVIDER_REVIEW_FAILED",
                "REVIEW_ATTACHMENT_FAILED", "REVIEW_CONTENT_INVALID",
                "REVIEW_ATTACHED"
            }
        ],
        "provider_cause_of_historical_failure": "NOT_RECORDED" if
            not manifest.get("review_failure_codes") else "SEE_SANITIZED_RECEIPT",
        "independent_review_completed": False,
        "source_verification_completed": False,
        "image_rights_confirmed": False,
        "publication_authorized": False,
        "requires_private_key_for_plaintext": True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only, no-key audit of a sealed handoff artifact")
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit_artifact(args.artifact)
    except EvidenceAuditError as exc:
        print(json.dumps({"archive_integrity": "FAIL", "reason": str(exc)}))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
