"""Fail-closed boundary for server-side atomic WordPress transitions.

This module does NOT implement locking inside WordPress. The injected
commit_if_unchanged callable MUST be a trusted server-side atomic compare-and-
swap transaction on post ID, expected draft digest, and a unique operation ID.
Plain WP REST GET+POST is NOT a valid implementation.
"""
from editorial_factual_certificate import verify_factual_certificate, draft_digest


def supervised_atomic_publish(post, certificate, signing_key, operation_id, commit_if_unchanged, *, now=None):
    if (not callable(commit_if_unchanged) or not isinstance(operation_id, str)
            or len(operation_id) < 16 or len(operation_id) > 128):
        return {"published": False, "reason": "atomic_backend_missing"}
    if not isinstance(post, dict) or post.get("status") != "draft":
        return {"published": False, "reason": "post_not_draft"}
    if not verify_factual_certificate(post, certificate, signing_key, now=now):
        return {"published": False, "reason": "factual_certificate_invalid"}
    digest = draft_digest(post)
    try:
        response = commit_if_unchanged(post["id"], digest, operation_id, certificate)
    except Exception:
        return {"published": False, "reason": "atomic_backend_failed"}
    if (not isinstance(response, dict) or response.get("committed") is not True
            or type(response.get("post_id")) is not int
            or response.get("post_id") != post["id"]
            or response.get("status") != "publish"):
        return {"published": False, "reason": "atomic_commit_not_confirmed"}
    return {"published": True, "post_id": post["id"], "operation_id": operation_id}
