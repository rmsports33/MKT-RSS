"""Supervised, read-only WordPress draft inspection.

Does not publish or change a draft. The fetch callable is injected so tests
cannot accidentally connect to production. Boolean editorial flags alone
cannot authorize publishing.
"""
from editorial_publish_gate import authorize_publish


def inspect_wordpress_draft(fetch_post, post_id, factual_review,
                            *, expected_category_id=10):
    if type(post_id) is not int or post_id <= 0:
        return {"authorized": False, "blockers": ["post_id_invalid"], "post": None}
    if not callable(fetch_post):
        return {"authorized": False, "blockers": ["fetch_post_missing"], "post": None}
    try:
        data = fetch_post(post_id)
    except Exception:
        return {"authorized": False, "blockers": ["wordpress_read_failed"], "post": None}
    if not isinstance(data, dict) or type(data.get("id")) is not int or data["id"] != post_id:
        return {"authorized": False, "blockers": ["wordpress_response_invalid"], "post": None}
    post = dict(data)
    for name in ("title", "content"):
        value = post.get(name)
        if isinstance(value, dict):
            post[name] = value.get("raw") or value.get("rendered") or ""
    result = authorize_publish(post, factual_review,
                               expected_category_id=expected_category_id)
    return {"authorized": result["autorizado"],
            "blockers": result["bloqueios"],
            "post": {"id": post_id, "status": post.get("status")}}
