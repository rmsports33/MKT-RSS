"""Classificador consultivo do catálogo de fontes de origem.

Correspondência de domínio é uma pista de descoberta, nunca aprovação factual.
Esta camada não consulta rede, não segue redirects e não transforma TLD em confiança.
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit

REGISTRY_SCHEMA = "conexo-editorial-primary-source-registry/1"
DEFAULT_REGISTRY = (Path(__file__).resolve().parent.parent /
                    "data" / "editorial-primary-source-registry-v1.json")
ROLES = {
    "primary_origin", "independent_measurement", "secondary_analysis",
    "interested_party_statement", "discovery_lead",
}
STATES = {"CONFIRMADA", "CORROBORADA", "ATRIBUIDA", "PROJETADA", "NAO_VERIFICADA"}
SOURCE_FIELDS = (
    "source_id", "url", "publisher", "source_type", "source_role",
    "published_at", "reference_period", "locator", "methodology",
    "limitations", "retrieved_at",
)


def _host(url: str) -> str:
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.port not in (None, 443)):
        raise ValueError("SOURCE_URL_INVALID")
    return parsed.hostname.lower().removeprefix("www.")


def load_registry(path=None) -> dict:
    target = Path(path) if path else DEFAULT_REGISTRY
    data = json.loads(target.read_text(encoding="utf-8"))
    if data.get("schema") != REGISTRY_SCHEMA or not isinstance(data.get("sources"), list):
        raise ValueError("SOURCE_REGISTRY_SCHEMA_INVALID")
    ids = set()
    for item in data["sources"]:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("SOURCE_REGISTRY_RECORD_INVALID")
        if item["id"] in ids:
            raise ValueError("SOURCE_REGISTRY_DUPLICATE_ID")
        ids.add(item["id"])
        if not isinstance(item.get("urls"), list) or not item["urls"]:
            raise ValueError("SOURCE_REGISTRY_URLS_MISSING")
        for url in item["urls"]:
            _host(url)
    return data


def classify_source_url(url: str, registry=None) -> dict:
    """Return a discovery hint. It never marks the URL or a claim verified."""
    host = _host(url)
    catalog = registry if registry is not None else load_registry()
    for record in catalog["sources"]:
        for candidate in record["urls"]:
            base = _host(candidate)
            if host == base or host.endswith("." + base):
                return {
                    "source_id": record["id"],
                    "publisher": record["publisher"],
                    "suggested_role": record.get("default_role", "discovery_lead"),
                    "topics": record.get("topics", []),
                    "registry_match": True,
                    "verification_status": "NAO_VERIFICADA",
                    "factual_verification_required": True,
                    "note": "Correspondência de catálogo não comprova a afirmação; julgar o papel por claim.",
                }
    return {
        "source_id": None,
        "publisher": None,
        "suggested_role": "discovery_lead",
        "topics": [],
        "registry_match": False,
        "verification_status": "NAO_VERIFICADA",
        "factual_verification_required": True,
        "note": "Fonte fora do catálogo; avaliar origem, escopo e método manualmente. TLD não é prova.",
    }


def validate_source_record(source: dict) -> list[str]:
    errors = []
    if not isinstance(source, dict):
        return ["SOURCE_RECORD_INVALID"]
    for field in SOURCE_FIELDS:
        if field not in source or source[field] is None or source[field] == "":
            errors.append("SOURCE_FIELD_MISSING:" + field)
    if source.get("source_role") not in ROLES:
        errors.append("SOURCE_ROLE_INVALID")
    try:
        _host(source.get("url", ""))
    except (ValueError, TypeError):
        errors.append("SOURCE_URL_INVALID")
    if source.get("methodology") in (None, ""):
        errors.append("SOURCE_METHODOLOGY_NOT_RECORDED")
    if source.get("limitations") in (None, ""):
        errors.append("SOURCE_LIMITATIONS_NOT_RECORDED")
    return errors


def validate_claim_record(claim: dict, sources: list[dict]) -> dict:
    """Validate traceability shape, not truth or semantic support."""
    if not isinstance(claim, dict):
        return {"status": "INVALID", "errors": ["CLAIM_RECORD_INVALID"]}
    errors = []
    for field in ("claim_id", "claim_text", "source_ids", "source_role", "verification_status"):
        if field not in claim or claim[field] in (None, "", []):
            errors.append("CLAIM_FIELD_MISSING:" + field)
    if claim.get("source_role") not in ROLES:
        errors.append("CLAIM_SOURCE_ROLE_INVALID")
    if claim.get("verification_status") not in STATES:
        errors.append("CLAIM_VERIFICATION_STATUS_INVALID")
    source_map = {s.get("source_id"): s for s in sources if isinstance(s, dict)}
    ids = claim.get("source_ids") if isinstance(claim.get("source_ids"), list) else []
    if not ids or any(source_id not in source_map for source_id in ids):
        errors.append("CLAIM_SOURCE_REFERENCE_INVALID")
    for source_id in ids:
        record = source_map.get(source_id)
        if record and record.get("source_role") not in ROLES:
            errors.append("CLAIM_SOURCE_RECORD_ROLE_INVALID")
    return {
        "status": "STRUCTURED_ONLY" if not errors else "INVALID",
        "errors": errors,
        "factuality_verified": False,
        "semantic_support_verified": False,
    }
