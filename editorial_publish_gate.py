"""Single fail-closed authorization point for WordPress publish transitions.

This module never performs a WordPress write. A caller MUST fetch the persisted
post after media/category updates and call this immediately before its own
status transition. No editorial queue state, missing evidence, or draft status
alone constitutes permission to publish.
"""
from editorial_wordpress_readiness import validate_wordpress_readiness


def authorize_publish(post: dict, factual_review: dict, *,
                      expected_category_id: int = 10) -> dict:
    readiness = validate_wordpress_readiness(
        post, expected_category_id=expected_category_id)
    problems = list(readiness.errors)
    if not isinstance(factual_review, dict):
        problems.append("factual_review_missing")
    else:
        if factual_review.get("veredito") != "APROVADO":
            problems.append("factual_review_not_approved")
        if factual_review.get("revisao_substantiva") is not True:
            problems.append("substantive_review_missing")
        if factual_review.get("evidencias_verificadas") is not True:
            problems.append("verified_evidence_missing")
        if factual_review.get("aprovacao_atual") is not True:
            problems.append("current_approval_missing")
    # A booleans-only factual_review is not independently certified.
    # Until a trusted, audited evidence contract is integrated, fail closed
    # even when every self-reported field is True.
    problems.append("trusted_factual_review_missing")
    return {"autorizado": False, "bloqueios": problems}


def require_publish_authorization(post: dict, factual_review: dict, **kwargs) -> None:
    result = authorize_publish(post, factual_review, **kwargs)
    if not result["autorizado"]:
        raise PermissionError("publicacao_bloqueada: " + ", ".join(result["bloqueios"]))
