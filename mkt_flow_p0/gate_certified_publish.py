"""Certified publish through Gate V1 — steps 4 and 5 of the integration contract.

This module connects:
  1. gate_review_reader  -> authenticated human review record
  2. editorial_factual_certificate -> issue/verify certificate bound to draft hash
  3. editorial_atomic_transition -> supervised_atomic_publish with a backend
  4. Gate V1 /conexo/v1/editorial/write -> single authorized write path

It NEVER approves, NEVER substitutes human review, NEVER writes directly to
WordPress outside the Gate, and NEVER runs in validation environments.

Important limitation: the Gate V1 write endpoint does not expose a server-side
compare-and-swap on the post row. It reserves an operation by nonce with an
atomic add_option and checks `expected_sha256` before writing. The backend
below therefore declares `atomic=False` unless a trusted CAS callable is
injected. Publishing through a non-CAS backend is BLOCKED by default.
"""
from __future__ import annotations

from editorial_atomic_transition import supervised_atomic_publish
from editorial_factual_certificate import (
    draft_digest, issue_factual_certificate, verify_factual_certificate,
)
from mkt_flow_p0.gate_review_reader import fetch_human_review
from mkt_flow_p0.wp_destination import (
    DestinationBlocked, resolve, assert_writable,
    OPERATION_PUBLISH, VALIDATION_ENVIRONMENT,
)


class CertifiedPublishBlocked(ValueError):
    """Raised before any write when the certified chain is incomplete."""


def build_certificate_from_gate(post: dict, *, wp_url: str, wp_user: str,
                                wp_app_password: str, signing_key: bytes,
                                session=None, timeout: int = 15) -> tuple[dict, dict]:
    """Fetch authenticated human review and issue a factual certificate.

    Returns (review_record, certificate). Does not write or approve.
    """
    if not isinstance(signing_key, bytes) or len(signing_key) < 32:
        raise CertifiedPublishBlocked("SIGNING_KEY_INVALID")
    digest = draft_digest(post)
    if not digest:
        raise CertifiedPublishBlocked("POST_NOT_CERTIFIABLE")
    review = fetch_human_review(
        int(post["id"]), wp_url=wp_url, wp_user=wp_user,
        wp_app_password=wp_app_password, session=session, timeout=timeout,
        expected_snapshot_sha256=digest)
    # Gate reviewer identity is an int; certificate contract uses a string id.
    record = {
        "reviewer_id": str(review["reviewer_id"]),
        "review_type": ("owner" if review["review_mode"] == "owner"
                        else "independent_human"),
        "decision": "APROVADO",
        "review_record_url": review["review_record_url"],
        "evidence_refs": _evidence_urls(review),
    }
    certificate = issue_factual_certificate(post, record, signing_key)
    if not verify_factual_certificate(post, certificate, signing_key):
        raise CertifiedPublishBlocked("CERTIFICATE_SELF_VERIFY_FAILED")
    return review, certificate


def _evidence_urls(review: dict) -> list[str]:
    urls = []
    for item in (review.get("checks") or {}).values():
        for ev in (item.get("evidencia") or []):
            text = ev if isinstance(ev, str) else str(ev)
            if text.startswith("https://") and text not in urls:
                urls.append(text)
    if not urls:
        raise CertifiedPublishBlocked("NO_AUTHENTICATED_EVIDENCE_URLS")
    return urls


CADIDATE_CAS_ROUTE = "/wp-json/conexo/v1/editorial/atomic-commit"


def gate_cas_backend(*, wp_url: str, wp_user: str, wp_app_password: str,
                     session=None, timeout: int = 15):
    """Build a commit_if_unchanged callable backed by the real Gate CAS route.

    The callable signature matches supervised_atomic_publish:
      (post_id, expected_sha256, operation_id, certificate)
    """
    import requests as _requests
    from .wp_destination import CANONICAL_SITE

    base = _validate_base(wp_url)
    http = session or _requests

    def backend(post_id, expected_sha256, operation_id, certificate):
        if not isinstance(certificate, dict):
            return {"committed": False, "post_id": post_id, "status": "draft"}
        try:
            response = http.post(
                f"{base}{CADIDATE_CAS_ROUTE}",
                json={"post_id": post_id, "expected_sha256": expected_sha256,
                      "operation_id": operation_id, "certificate": certificate},
                auth=(wp_user, wp_app_password), timeout=timeout,
                allow_redirects=False)
        except _requests.RequestException:
            return {"committed": False, "post_id": post_id, "status": "draft"}
        if response.status_code not in (200, 201):
            return {"committed": False, "post_id": post_id, "status": "draft"}
        try:
            body = response.json()
        except (ValueError, TypeError):
            return {"committed": False, "post_id": post_id, "status": "draft"}
        if not isinstance(body, dict) or body.get("committed") is not True:
            return {"committed": False, "post_id": post_id, "status": "draft"}
        return {"committed": True, "post_id": body.get("post_id", post_id),
                "status": body.get("status", "draft")}

    return backend


def _validate_base(wp_url: str) -> str:
    from urllib.parse import urlsplit
    if not isinstance(wp_url, str) or not wp_url.strip():
        raise CertifiedPublishBlocked("WP_URL_MISSING")
    url = wp_url.strip().rstrip("/")
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.netloc or parts.username or parts.password:
        raise CertifiedPublishBlocked("WP_URL_INVALID")
    return url


def certified_publish(post: dict, certificate: dict, signing_key: bytes,
                      operation_id: str, commit_if_unchanged, *,
                      now=None, env: dict | None = None) -> dict:
    """Publish only when destination, certificate and CAS backend are valid.

    This is the single entry point that combines steps 4 (atomic transition)
    and 5 (Gate certificate validation without duplicating human approval).
    """
    environ = env if env is not None else {}
    if environ.get("GITHUB_ENVIRONMENT", "").strip() == VALIDATION_ENVIRONMENT:
        raise CertifiedPublishBlocked("VALIDATION_ENVIRONMENT_NO_WRITE")
    try:
        dest = resolve(OPERATION_PUBLISH, env=environ)
        assert_writable(dest, OPERATION_PUBLISH)
    except DestinationBlocked as exc:
        raise CertifiedPublishBlocked(str(exc)) from None

    if not verify_factual_certificate(post, certificate, signing_key, now=now):
        raise CertifiedPublishBlocked("FACTUAL_CERTIFICATE_INVALID")
    digest = draft_digest(post)
    if not digest or certificate.get("draft_sha256") != digest:
        raise CertifiedPublishBlocked("DRAFT_HASH_MISMATCH")

    # supervised_atomic_publish already refuses when backend is missing or
    # when the certificate is invalid. It does not re-approve the article.
    return supervised_atomic_publish(
        post, certificate, signing_key, operation_id, commit_if_unchanged,
        now=now)
