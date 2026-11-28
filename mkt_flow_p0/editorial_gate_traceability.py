"""Build a version-bound traceability sidecar for a future Gate consumer.

This sidecar is deliberately separate from cxeg-package:v1. The RC10.5 Gate
contract has an exact six-field manifest; adding fields would correctly fail
its strict validator. This module therefore creates an auditable handoff
artifact, never a Gate approval, WordPress write, signature, or publication.
"""
from __future__ import annotations

import hashlib
import json
import re

SCHEMA = "conexo-editorial-gate-traceability-sidecar/1"
CONTRACT_SHA256 = "6b55c87c15b004169a77a73d3064fb02072c1cc370e7c9be68bee20e9abde9f7"


def canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def build_gate_traceability_sidecar(
    article_markdown: str,
    evidence_dossier: dict,
    primary_review: dict,
    asve_receipt: dict,
    internal_pages: list[dict],
    decisions: list[dict] | None = None,
    *,
    contract_sha256: str = CONTRACT_SHA256,
    run_id: str | None = None,
) -> dict:
    """Create a hash-linked sidecar. Structural validation is not fact-checking."""
    from mkt_flow_p0.editorial_secondary_analysis import (
        RECEIPT_SCHEMA,
        build_analysis_request,
        validate_dispositions,
    )
    from mkt_flow_p0.primary_source_registry import (
        validate_claim_record,
        validate_source_record,
    )

    if not isinstance(contract_sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", contract_sha256):
        raise ValueError("GATE_TRACE_CONTRACT_HASH_INVALID")
    request = build_analysis_request(article_markdown, evidence_dossier, internal_pages)
    article_hash = request["article_sha256"]
    if not isinstance(primary_review, dict) or not primary_review:
        raise ValueError("GATE_TRACE_PRIMARY_REVIEW_REQUIRED")
    if not isinstance(asve_receipt, dict) or asve_receipt.get("schema") != RECEIPT_SCHEMA:
        raise ValueError("GATE_TRACE_ASVE_RECEIPT_REQUIRED")
    if asve_receipt.get("article_sha256") != article_hash:
        raise ValueError("GATE_TRACE_ARTICLE_VERSION_MISMATCH")

    sources = evidence_dossier.get("sources", [])
    claims = evidence_dossier.get("claims", [])
    source_errors = []
    for source in sources:
        source_errors.extend(validate_source_record(source))
    if source_errors:
        raise ValueError("GATE_TRACE_SOURCE_DOSSIER_INCOMPLETE:" + ",".join(source_errors))
    claim_errors = []
    for claim in claims:
        validated = validate_claim_record(claim, sources)
        claim_errors.extend(validated["errors"])
    if claim_errors:
        raise ValueError("GATE_TRACE_CLAIMS_INCOMPLETE:" + ",".join(claim_errors))

    decisions = decisions or []
    disposition = validate_dispositions(asve_receipt, decisions)
    findings = asve_receipt.get("findings", [])
    if (not isinstance(findings, list) or len(findings) > 5
            or asve_receipt.get("finding_count") != len(findings)
            or asve_receipt.get("rewrote_article") is not False
            or asve_receipt.get("publication_authorized") is not False):
        raise ValueError("GATE_TRACE_ASVE_RECEIPT_INVALID")
    allowed_sources = set(request.get("allowed_source_ids", []))
    allowed_claims = set(request.get("allowed_claim_ids", []))
    allowed_pages = set(request.get("allowed_internal_page_ids", []))
    finding_ids = set()
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError("GATE_TRACE_ASVE_FINDING_INVALID")
        fid = finding.get("finding_id")
        if not isinstance(fid, str) or not fid or fid in finding_ids:
            raise ValueError("GATE_TRACE_ASVE_FINDING_ID_INVALID")
        finding_ids.add(fid)
        if (not set(finding.get("evidence_refs", [])) <= allowed_sources
                or not set(finding.get("claim_refs", [])) <= allowed_claims
                or not set(finding.get("internal_page_refs", [])) <= allowed_pages):
            raise ValueError("GATE_TRACE_ASVE_UNKNOWN_REFERENCE")
    p0 = [f["finding_id"] for f in findings if f.get("priority") == "P0"]
    p1 = [f["finding_id"] for f in findings if f.get("priority") == "P1"]
    p2 = [f["finding_id"] for f in findings if f.get("priority") == "P2"]
    primary_verdict = str(primary_review.get("veredito") or "")
    if p0:
        handoff = "BLOCKED_P0_REQUIRES_NEW_ARTICLE_VERSION"
    elif disposition["status"] != "CLOSED":
        handoff = "EDITORIAL_DECISION_REQUIRED"
    elif primary_verdict != "APTO_PARA_APROVACAO":
        handoff = "PRIMARY_REVIEW_NOT_READY"
    else:
        handoff = "TRACEABILITY_COMPLETE_FOR_GATE_CONSUMER"

    body = {
        "schema": SCHEMA,
        "contract_sha256": contract_sha256,
        "article_sha256": article_hash,
        "evidence_dossier_sha256": digest(evidence_dossier),
        "primary_review_sha256": digest(primary_review),
        "asve_receipt_sha256": digest(asve_receipt),
        "decisions_sha256": digest(decisions),
        "source_ids": sorted(source["source_id"] for source in sources),
        "claim_ids": sorted(claim["claim_id"] for claim in claims),
        "verification_statuses": sorted({
            str(claim.get("verification_status")) for claim in claims
        }),
        "primary_review_verdict": str(primary_review.get("veredito") or
                                       primary_review.get("veredito_revisao_principal") or "NOT_PROVIDED"),
        "asve_finding_ids": {
            "P0": sorted(p0), "P1": sorted(p1), "P2": sorted(p2)
        },
        "asve_decision_status": disposition["status"],
        "handoff_status": handoff,
        "gate_contract_compatibility": {
            "current_contract": "cxeg-package:v1",
            "current_gate_accepts_sidecar": False,
            "transport": "separate_private_sidecar",
            "requires_future_gate_consumer": True
        },
        "factuality_verified_by_sidecar": False,
        "human_approval_verified_by_sidecar": False,
        "publication_authorized": False
    }
    if run_id is not None:
        if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", run_id):
            raise ValueError("GATE_TRACE_RUN_ID_INVALID")
        body["run_id"] = run_id
    body["sidecar_sha256"] = digest(body)
    return body


def validate_gate_traceability_sidecar(sidecar: dict) -> dict:
    if not isinstance(sidecar, dict) or sidecar.get("schema") != SCHEMA:
        raise ValueError("GATE_TRACE_SCHEMA_INVALID")
    expected = sidecar.get("sidecar_sha256")
    body = {k: v for k, v in sidecar.items() if k != "sidecar_sha256"}
    if not isinstance(expected, str) or not re.fullmatch(r"[a-f0-9]{64}", expected):
        raise ValueError("GATE_TRACE_HASH_FORMAT_INVALID")
    if digest(body) != expected:
        raise ValueError("GATE_TRACE_HASH_MISMATCH")
    if sidecar.get("publication_authorized") is not False:
        raise ValueError("GATE_TRACE_PUBLICATION_FLAG_INVALID")
    compatibility = sidecar.get("gate_contract_compatibility")
    if not isinstance(compatibility, dict) or compatibility.get("current_gate_accepts_sidecar") is not False:
        raise ValueError("GATE_TRACE_FALSE_GATE_COMPATIBILITY")
    if compatibility.get("current_contract") != "cxeg-package:v1":
        raise ValueError("GATE_TRACE_GATE_CONTRACT_INVALID")
    if "run_id" in sidecar and (
            not isinstance(sidecar["run_id"], str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", sidecar["run_id"])):
        raise ValueError("GATE_TRACE_RUN_ID_INVALID")
    return {
        "valid": True,
        "sidecar_sha256": expected,
        "article_sha256": sidecar.get("article_sha256"),
        "handoff_status": sidecar.get("handoff_status"),
        "gate_acceptance": "NOT_IMPLEMENTED_IN_CXEG_PACKAGE_V1",
        "publication_authorized": False,
    }
