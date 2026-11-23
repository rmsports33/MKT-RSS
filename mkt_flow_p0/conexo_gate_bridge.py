"""Strict MKT-RSS -> Conexo Editorial Gate v3 contract adapter.

This module only validates and assembles REST payloads. It performs no network
calls, WordPress writes, approvals, signatures, or publication.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any
from urllib.parse import urlparse

from mkt_flow_p0.revisor_qualidade_unico import (
    GATE_REQUIRED_CHECKS,
    GATE_VERSAO,
    fingerprint_artigo,
)

GATE_BRIEF_SCHEMA = "conexo-editorial-brief/2"
GATE_POLICY_VERSION = "conexo-editorial-requirements/1"
GATE_SNAPSHOT_FINGERPRINT_VERSION = "cxeg-editorial-fingerprint-v2"
GATE_SNAPSHOT_DIGEST_VERSION = "cxeg-snapshot-digest-v2"

FINGERPRINT_FIELDS = (
    "post_id", "post_type", "slug", "title", "content", "excerpt",
    "author_id", "categories", "tags", "featured_media",
)
SNAPSHOT_FIELDS = (
    "post_id", "post_type", "post_status", "slug", "title", "content",
    "excerpt", "author_id", "date_gmt", "categories", "tags", "featured_media",
)

BRIEF_FIELDS = ("genre", "persona", "reader", "need", "angle", "contribution", "limits")
LEGACY_BRIEF_FIELDS = ("genre", "reader", "need", "angle", "contribution", "limits")
GENRES = {"noticia", "guia", "analise", "comparativo", "review", "nota_breve"}

HUMAN_EVIDENCE_TYPES = {"url", "snapshot", "attachment", "screenshot"}
ATTACHMENT_TYPES = {"attachment", "screenshot"}
SOURCE_REQUIRED = {"licenca_imagem", "fontes", "alegacoes", "links_internos", "seo"}
SNAPSHOT_REQUIRED = {
    "versao", "titulo", "categoria", "voz_editorial", "persona", "html",
}
SCREENSHOT_REQUIRED = {"visual_390", "visual_1440"}
INTERNAL_IMAGE_REQUIRED = {"imagens_internas"}
COVER_REQUIRED = {"capa"}

_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.I,
)
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _canonical_json(value: Any) -> str:
    """Mirror the Gate's restricted CanonicalJson profile (no floats/objects)."""
    def validate(item: Any) -> None:
        if isinstance(item, float):
            raise ValueError("floating_point_not_allowed_in_gate_contract")
        if item is None or type(item) in (str, int, bool):
            return
        if isinstance(item, list):
            for child in item:
                validate(child)
            return
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise ValueError("gate_object_keys_must_be_strings")
            for child in item.values():
                validate(child)
            return
        raise ValueError("unsupported_value_in_gate_contract")

    validate(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _hash_fields(snapshot: dict, fields: tuple[str, ...], version: str) -> str:
    selected = {}
    for field in fields:
        if field not in snapshot:
            raise ValueError("gate_snapshot_missing_" + field)
        selected[field] = snapshot[field]
    raw = version + "\n" + _canonical_json(selected)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def gate_snapshot_fingerprint(snapshot: dict) -> str:
    return _hash_fields(snapshot, FINGERPRINT_FIELDS, GATE_SNAPSHOT_FINGERPRINT_VERSION)


def gate_snapshot_digest(snapshot: dict) -> str:
    return _hash_fields(snapshot, SNAPSHOT_FIELDS, GATE_SNAPSHOT_DIGEST_VERSION)


def normalize_gate_brief(legacy_brief: dict, *, persona_profile: str) -> dict:
    """Preserve the MKT six-field brief and add a separately supplied persona.

    Persona is never inferred from 'reader'. The Gate v2 brief requires an
    explicit seven-field object and a 20..1200 character persona profile.
    """
    if not isinstance(legacy_brief, dict) or set(legacy_brief) != set(LEGACY_BRIEF_FIELDS):
        raise ValueError("mkt_brief_must_match_canonical_six_field_schema")
    if legacy_brief.get("genre") not in GENRES:
        raise ValueError("unsupported_editorial_genre")
    for field in LEGACY_BRIEF_FIELDS:
        if field == "genre":
            continue
        value = legacy_brief.get(field)
        if not isinstance(value, str) or not 20 <= len(value.strip()) <= 1200:
            raise ValueError("invalid_mkt_brief_field_" + field)
    if not isinstance(persona_profile, str) or not 20 <= len(persona_profile.strip()) <= 1200:
        raise ValueError("explicit_persona_profile_required")
    result = {
        "genre": legacy_brief["genre"],
        "persona": persona_profile.strip(),
        "reader": legacy_brief["reader"].strip(),
        "need": legacy_brief["need"].strip(),
        "angle": legacy_brief["angle"].strip(),
        "contribution": legacy_brief["contribution"].strip(),
        "limits": legacy_brief["limits"].strip(),
    }
    if set(result) != set(BRIEF_FIELDS):
        raise ValueError("gate_brief_schema_mismatch")
    return result


def _raw_post_value(post: dict, key: str, *, require_raw: bool = False):
    value = post.get(key)
    if isinstance(value, dict):
        if require_raw and "raw" not in value:
            raise ValueError("wordpress_native_raw_readback_required_" + key)
        if "raw" in value:
            return value["raw"]
        return value.get("rendered")
    if require_raw:
        raise ValueError("wordpress_native_raw_readback_required_" + key)
    return value


def _utc_mysql(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("wordpress_gmt_date_missing")
    raw = value.strip()
    try:
        if raw.endswith("Z"):
            parsed = datetime.fromisoformat(raw[:-1] + "+00:00")
        else:
            parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            # WordPress date_gmt is explicitly UTC even when REST omits the Z.
            parsed = parsed.replace(tzinfo=timezone.utc)
        parsed = parsed.astimezone(timezone.utc)
    except ValueError as error:
        raise ValueError("wordpress_gmt_date_invalid") from error
    if parsed.year < 1970:
        raise ValueError("wordpress_gmt_date_invalid")
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def _normalized_wp_post(post: dict) -> dict:
    if not isinstance(post, dict):
        raise ValueError("authenticated_wordpress_post_required")
    content = _raw_post_value(post, "content", require_raw=True)
    title = _raw_post_value(post, "title", require_raw=True)
    excerpt = _raw_post_value(post, "excerpt", require_raw=True)
    if not all(isinstance(value, str) for value in (content, title, excerpt)):
        raise ValueError("wordpress_raw_content_title_excerpt_must_be_strings")

    categories = post.get("categories")
    tags = post.get("tags")
    if not isinstance(categories, list) or not isinstance(tags, list):
        raise ValueError("wordpress_categories_and_tags_required")
    if any(type(value) is not int or value < 1 for value in categories + tags):
        raise ValueError("wordpress_taxonomy_ids_invalid")

    post_id = post.get("id")
    author = post.get("author")
    featured = post.get("featured_media")
    post_type = post.get("type")
    status = post.get("status")
    if type(post_id) is not int or post_id < 1:
        raise ValueError("wordpress_post_id_invalid")
    if type(author) is not int or author < 1:
        raise ValueError("wordpress_author_id_invalid")
    if type(featured) is not int or featured < 0:
        raise ValueError("wordpress_featured_media_invalid")
    if not isinstance(post_type, str) or not post_type or not isinstance(status, str) or not status:
        raise ValueError("wordpress_post_type_or_status_invalid")
    slug = post.get("slug")
    if not isinstance(slug, str):
        raise ValueError("wordpress_slug_invalid")

    return {
        "post_id": post_id,
        "post_type": post_type,
        "post_status": status,
        "slug": slug,
        "title": title,
        "content": content,
        "excerpt": excerpt,
        "author_id": author,
        "date_gmt": _utc_mysql(post.get("date_gmt")),
        "categories": sorted(set(categories)),
        "tags": sorted(set(tags)),
        "featured_media": featured,
    }


def validate_gate_snapshot(snapshot: dict) -> dict:
    if not isinstance(snapshot, dict):
        raise ValueError("persisted_gate_snapshot_required")
    required = set(SNAPSHOT_FIELDS) | {
        "snapshot_id", "snapshot_sha256", "snapshot_digest_version",
        "fingerprint_version", "fingerprint_sha256",
    }
    if set(snapshot) < required:
        missing = sorted(required - set(snapshot))
        raise ValueError("gate_snapshot_missing_fields:" + ",".join(missing))
    if not isinstance(snapshot.get("snapshot_id"), str) or not _UUID.fullmatch(snapshot["snapshot_id"]):
        raise ValueError("gate_snapshot_id_invalid")
    if snapshot.get("snapshot_digest_version") != GATE_SNAPSHOT_DIGEST_VERSION:
        raise ValueError("gate_snapshot_digest_version_mismatch")
    if snapshot.get("fingerprint_version") != GATE_SNAPSHOT_FINGERPRINT_VERSION:
        raise ValueError("gate_snapshot_fingerprint_version_mismatch")
    if not isinstance(snapshot.get("snapshot_sha256"), str) or not _SHA256.fullmatch(snapshot["snapshot_sha256"]):
        raise ValueError("gate_snapshot_digest_invalid")
    if not isinstance(snapshot.get("fingerprint_sha256"), str) or not _SHA256.fullmatch(snapshot["fingerprint_sha256"]):
        raise ValueError("gate_snapshot_fingerprint_invalid")
    if snapshot.get("snapshot_sha256") != gate_snapshot_digest(snapshot):
        raise ValueError("gate_snapshot_digest_mismatch")
    if snapshot.get("fingerprint_sha256") != gate_snapshot_fingerprint(snapshot):
        raise ValueError("gate_snapshot_fingerprint_mismatch")
    if type(snapshot.get("post_id")) is not int or snapshot["post_id"] < 1:
        raise ValueError("gate_snapshot_post_id_invalid")
    if snapshot.get("post_type") != "post" or snapshot.get("post_status") not in {"draft", "pending"}:
        raise ValueError("gate_snapshot_outside_supported_lifecycle")
    return snapshot


def validate_wordpress_post_matches_gate_snapshot(post: dict, snapshot: dict) -> None:
    """Require native WP edit-context raw fields to match the Gate snapshot."""
    normalized = _normalized_wp_post(post)
    for field in SNAPSHOT_FIELDS:
        if normalized[field] != snapshot[field]:
            raise ValueError("wordpress_readback_mismatch_" + field)


def _valid_observed_at(value: Any) -> bool:
    if not isinstance(value, str) or not _UTC.fullmatch(value):
        return False
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%dT%H:%M:%SZ") == value
    except ValueError:
        return False


def _validate_gate_evidence(check_name: str, evidence: Any, snapshot_id: str) -> dict:
    if not isinstance(evidence, dict):
        raise ValueError("gate_human_evidence_must_be_object_" + check_name)
    allowed = {"tipo", "referencia", "descricao", "observado_em", "attachment_id", "sha256"}
    required = {"tipo", "referencia", "descricao", "observado_em"}
    if set(evidence) - allowed or not required.issubset(evidence):
        raise ValueError("gate_human_evidence_shape_invalid_" + check_name)
    kind = evidence["tipo"]
    reference = evidence["referencia"]
    description = evidence["descricao"]
    if kind not in HUMAN_EVIDENCE_TYPES:
        raise ValueError("gate_human_evidence_type_invalid_" + check_name)
    if not isinstance(reference, str) or not 8 <= len(reference.strip()) <= 2048:
        raise ValueError("gate_human_evidence_reference_invalid_" + check_name)
    if not isinstance(description, str) or not 8 <= len(description.strip()) <= 2000:
        raise ValueError("gate_human_evidence_description_invalid_" + check_name)
    if not _valid_observed_at(evidence["observado_em"]):
        raise ValueError("gate_human_evidence_timestamp_invalid_" + check_name)

    if kind == "url":
        parsed = urlparse(reference)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("gate_evidence_requires_safe_https_url_" + check_name)
    elif kind == "snapshot":
        if not re.fullmatch(
            r"snapshot:" + re.escape(snapshot_id) + r"#[a-z0-9_-]+",
            reference,
            re.I,
        ):
            raise ValueError("gate_snapshot_evidence_must_bind_exact_snapshot_" + check_name)
    else:
        attachment_id = evidence.get("attachment_id")
        sha = evidence.get("sha256")
        if (
            type(attachment_id) is not int
            or attachment_id < 1
            or reference != "wp-attachment:" + str(attachment_id)
            or not isinstance(sha, str)
            or not _SHA256.fullmatch(sha)
        ):
            raise ValueError("gate_attachment_evidence_invalid_" + check_name)

    if check_name in SCREENSHOT_REQUIRED and kind != "screenshot":
        raise ValueError("gate_visual_review_requires_screenshot_" + check_name)
    if check_name == "capa" and kind != "attachment":
        raise ValueError("gate_cover_requires_featured_image_attachment")
    if check_name in SOURCE_REQUIRED and kind not in {"url", "attachment"}:
        raise ValueError("gate_source_reference_required_" + check_name)
    if check_name in SNAPSHOT_REQUIRED and kind not in {"snapshot", "url", "attachment", "screenshot"}:
        raise ValueError("gate_snapshot_reference_required_" + check_name)
    if check_name in INTERNAL_IMAGE_REQUIRED and kind not in {"snapshot", "attachment"}:
        raise ValueError("gate_inline_image_reference_required")
    if check_name in {"visual_390", "visual_1440"} and kind != "screenshot":
        raise ValueError("gate_visual_screenshot_required")

    # Do not pass unknown evidence members to the Gate.
    normalized = {key: evidence[key] for key in required}
    if kind in ATTACHMENT_TYPES:
        normalized["attachment_id"] = evidence["attachment_id"]
        normalized["sha256"] = evidence["sha256"]
    return normalized


def _validate_mkt_report(report: dict, post: dict) -> str:
    if not isinstance(report, dict) or report.get("schema") != GATE_VERSAO:
        raise ValueError("independent_reviewer_v2_report_required")
    if report.get("post_id") != post.get("id"):
        raise ValueError("reviewer_report_post_id_mismatch")
    if report.get("fingerprint") != fingerprint_artigo(post):
        raise ValueError("reviewer_report_fingerprint_mismatch")
    if report.get("veredito") != "APTO_PARA_APROVACAO":
        raise ValueError("independent_reviewer_did_not_pass:" + str(report.get("veredito")))
    if report.get("publication_authorized") is not False or report.get("publicacao_autorizada") is not False:
        raise ValueError("reviewer_report_must_not_authorize_publication")
    if not isinstance(report.get("reviewer"), str) or not report["reviewer"].strip():
        raise ValueError("reviewer_identity_label_missing")
    checks = report.get("checks")
    if not isinstance(checks, dict) or set(checks) != set(GATE_REQUIRED_CHECKS):
        raise ValueError("reviewer_v2_required_check_matrix_mismatch")
    for key in GATE_REQUIRED_CHECKS:
        check = checks[key]
        if not isinstance(check, dict) or check.get("estado") != "VERIFICADO":
            raise ValueError("reviewer_check_not_verified_" + key)
    return report["reviewer"]


def build_gate_quality_record_request(
    *,
    wordpress_post: dict,
    gate_snapshot: dict,
    reviewer_report: dict,
    mkt_brief: dict,
    persona_profile: str,
    gate_human_evidence: dict,
    reviewer_key_id: str,
) -> dict:
    """Build the payload for POST /conexo/v2/quality-records; never calls it.

    Both the WordPress edit-context raw readback and the stored Gate snapshot
    are checked before any MKT reviewer report is accepted. All 16 evidence
    groups must be explicit, typed, version-bound and attributable to the
    same reviewer label and the exact Gate snapshot.
    """
    snapshot = validate_gate_snapshot(gate_snapshot)
    validate_wordpress_post_matches_gate_snapshot(wordpress_post, snapshot)
    reviewer_label = _validate_mkt_report(reviewer_report, wordpress_post)

    brief = normalize_gate_brief(mkt_brief, persona_profile=persona_profile)
    if not isinstance(reviewer_key_id, str) or not 1 <= len(reviewer_key_id) <= 100:
        raise ValueError("reviewer_key_id_required")

    if not isinstance(gate_human_evidence, dict) or set(gate_human_evidence) != set(GATE_REQUIRED_CHECKS):
        raise ValueError("all_16_gate_human_evidence_groups_required")

    checks = {}
    for name in GATE_REQUIRED_CHECKS:
        group = gate_human_evidence[name]
        if not isinstance(group, dict):
            raise ValueError("gate_human_evidence_group_invalid_" + name)
        if group.get("estado") != "VERIFICADO":
            raise ValueError("gate_human_evidence_not_verified_" + name)
        if group.get("reviewer") != reviewer_label:
            raise ValueError("gate_human_evidence_reviewer_mismatch_" + name)
        if group.get("fingerprint") != reviewer_report["fingerprint"]:
            raise ValueError("gate_human_evidence_mkt_fingerprint_mismatch_" + name)
        raw_items = group.get("evidencia")
        if not isinstance(raw_items, list) or not 1 <= len(raw_items) <= 12:
            raise ValueError("gate_human_evidence_list_invalid_" + name)
        normalized_items = [
            _validate_gate_evidence(name, item, snapshot["snapshot_id"])
            for item in raw_items
        ]
        checks[name] = {
            "estado": "VERIFICADO",
            "origem": "humana",
            "evidencia": normalized_items,
        }

    return {
        "post_id": snapshot["post_id"],
        "snapshot_id": snapshot["snapshot_id"],
        "checks": checks,
        "reviewer_key_id": reviewer_key_id,
        "policy_version": GATE_POLICY_VERSION,
        "brief": brief,
        "publication_authorized": False,
        "factual_approval": False,
        "contract": "conexo-quality-record/3",
        "brief_schema": GATE_BRIEF_SCHEMA,
    }


def build_gate_assessment_request(*, gate_snapshot: dict, mkt_brief: dict, persona_profile: str) -> dict:
    """Build the advisory REST preflight payload for POST /quality-assessments."""
    snapshot = validate_gate_snapshot(gate_snapshot)
    brief = normalize_gate_brief(mkt_brief, persona_profile=persona_profile)
    return {
        "post_id": snapshot["post_id"],
        "snapshot_id": snapshot["snapshot_id"],
        "brief": brief,
        "publication_authorized": False,
    }
