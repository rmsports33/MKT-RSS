"""Authenticated read-only client for the Gate V1 human review record.

Contract (Gate V1 RC10.4, active installation):
  GET /wp-json/conexo/v1/editorial/quality/{id}
  -> {"post_id", "valid_for_current_version", "report": {...}|null}

The record contains: schema, post_id, snapshot_sha256, fingerprint, veredito,
checks (with human evidence), reviewer_id, reviewed_at, review_mode.

This module NEVER writes and NEVER approves. It only fetches and validates the
human review record so the MKT-RSS factual certificate can bind to it.
Authentication uses the existing WordPress application password; credentials
come from the executor environment, never from chat or source code.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

import requests

_SHA = re.compile(r"^[a-f0-9]{64}$")


class ReviewReadBlocked(ValueError):
    """Raised before/after a read when the review record is not trustworthy."""


def _validate_target(wp_url: str) -> str:
    if not isinstance(wp_url, str) or not wp_url.strip():
        raise ReviewReadBlocked("WP_URL_MISSING")
    url = wp_url.strip().rstrip("/")
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.netloc:
        raise ReviewReadBlocked("WP_URL_NOT_HTTPS")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise ReviewReadBlocked("WP_URL_INVALID")
    return url


def fetch_human_review(post_id: int, *, wp_url: str, wp_user: str,
                       wp_app_password: str, session=requests,
                       timeout: int = 15, expected_snapshot_sha256: str = "") -> dict:
    """Fetch and validate a Gate V1 human review record for `post_id`.

    Returns a normalized dict with the fields required by the factual
    certificate. Fails closed on auth errors, missing report, stale version,
    missing reviewer identity/evidence, or invalid schema.
    """
    if type(post_id) is not int or post_id < 1:
        raise ReviewReadBlocked("POST_ID_INVALID")
    if not wp_user or not wp_app_password:
        raise ReviewReadBlocked("WP_CREDENTIALS_MISSING")
    if expected_snapshot_sha256 and (not isinstance(expected_snapshot_sha256, str)
                                     or not _SHA.fullmatch(expected_snapshot_sha256)):
        raise ReviewReadBlocked("EXPECTED_SHA_INVALID")
    base = _validate_target(wp_url)
    url = f"{base}/wp-json/conexo/v1/editorial/quality/{post_id}"

    try:
        response = session.get(url, auth=(wp_user, wp_app_password),
                               timeout=timeout, allow_redirects=False)
    except requests.RequestException:
        raise ReviewReadBlocked("WP_READ_OUTCOME_UNKNOWN") from None
    if response.status_code == 401:
        raise ReviewReadBlocked("WP_READ_UNAUTHORIZED")
    if response.status_code == 403:
        raise ReviewReadBlocked("WP_READ_FORBIDDEN")
    if response.status_code != 200:
        raise ReviewReadBlocked("WP_READ_HTTP_REJECTED")
    try:
        body = response.json()
    except (ValueError, TypeError):
        raise ReviewReadBlocked("WP_READ_INVALID_JSON") from None
    if not isinstance(body, dict):
        raise ReviewReadBlocked("WP_READ_INVALID_BODY")

    report = body.get("report")
    if not isinstance(report, dict):
        raise ReviewReadBlocked("HUMAN_REVIEW_RECORD_MISSING")
    if body.get("post_id") != post_id or report.get("post_id") != post_id:
        raise ReviewReadBlocked("HUMAN_REVIEW_POST_MISMATCH")
    if report.get("schema") != "conexo-article-quality/1":
        raise ReviewReadBlocked("HUMAN_REVIEW_SCHEMA_INVALID")
    if report.get("veredito") != "APTO_PARA_APROVACAO":
        raise ReviewReadBlocked("HUMAN_REVIEW_NOT_APPROVED")
    if body.get("valid_for_current_version") is not True:
        raise ReviewReadBlocked("HUMAN_REVIEW_STALE_FOR_CURRENT_VERSION")

    snapshot_sha = report.get("snapshot_sha256")
    if not isinstance(snapshot_sha, str) or not _SHA.fullmatch(snapshot_sha):
        raise ReviewReadBlocked("HUMAN_REVIEW_SHA_INVALID")
    if expected_snapshot_sha256 and snapshot_sha != expected_snapshot_sha256:
        raise ReviewReadBlocked("HUMAN_REVIEW_SHA_MISMATCH")

    reviewer_id = report.get("reviewer_id")
    if type(reviewer_id) is not int or reviewer_id < 1:
        raise ReviewReadBlocked("HUMAN_REVIEW_REVIEWER_INVALID")
    if not isinstance(report.get("reviewed_at"), int) or report["reviewed_at"] <= 0:
        raise ReviewReadBlocked("HUMAN_REVIEW_DATE_INVALID")
    if report.get("review_mode") not in ("independent", "owner"):
        raise ReviewReadBlocked("HUMAN_REVIEW_MODE_INVALID")

    checks = report.get("checks")
    if not isinstance(checks, dict) or not checks:
        raise ReviewReadBlocked("HUMAN_REVIEW_CHECKS_MISSING")
    for key, item in checks.items():
        if not isinstance(item, dict) or item.get("estado") != "VERIFICADO":
            raise ReviewReadBlocked("HUMAN_REVIEW_CHECK_NOT_VERIFIED")
        evidence = item.get("evidencia")
        if not isinstance(evidence, list) or not evidence:
            raise ReviewReadBlocked("HUMAN_REVIEW_EVIDENCE_MISSING")

    return {
        "post_id": post_id,
        "snapshot_sha256": snapshot_sha,
        "reviewer_id": reviewer_id,
        "reviewed_at": report["reviewed_at"],
        "review_mode": report["review_mode"],
        "fingerprint": report.get("fingerprint", ""),
        "checks": checks,
        "source": "gate-v1-human-review",
        "review_record_url": f"{base}/wp-json/conexo/v1/editorial/quality/{post_id}",
    }
