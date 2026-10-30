"""Offline WordPress transition guard.

No network requests or writes. The caller must supply a freshly fetched draft
and an independently verified editorial decision. This does not establish
atomicity: WordPress REST lacks an expected-version compare-and-swap here.
"""
from editorial_publish_gate import authorize_publish


def plan_publish_transition(post: dict, factual_review: dict, *,
                            expected_category_id: int = 10) -> dict:
    result = authorize_publish(post, factual_review,
                               expected_category_id=expected_category_id)
    if not result["autorizado"]:
        return {"allowed": False, "errors": result["bloqueios"], "request": None}
    # Editorial flags alone are self-asserted: no trusted approval identity,
    # provenance, or concurrency guard has been verified. Never emit a
    # ready-to-send publication request from this offline planner.
    return {"allowed": False,
            "errors": ["trusted_approval_and_atomic_transition_missing"],
            "request": None}


def verify_publish_readback(expected_id: int, response: dict) -> bool:
    return (type(expected_id) is int and expected_id > 0
            and isinstance(response, dict)
            and response.get("id") == expected_id
            and response.get("status") == "publish")
