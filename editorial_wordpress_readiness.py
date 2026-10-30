"""Fail-closed readiness validation for WordPress news articles.

Use this check after saving a draft and before changing its status to publish.
It deliberately makes no network calls or WordPress writes.
"""
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class Readiness:
    ready: bool
    errors: tuple[str, ...]


def validate_wordpress_readiness(post: dict, *, expected_category_id: int = 10,
                                 expected_site: str = "conexotech.com.br") -> Readiness:
    errors = []
    if not isinstance(post, dict):
        return Readiness(False, ("post_missing",))
    if post.get("status") not in ("draft", "pending", "future"):
        errors.append("unexpected_status")
    if expected_category_id not in (post.get("categories") or []):
        errors.append("news_category_missing")
    if 1 in (post.get("categories") or []):
        errors.append("uncategorized_present")
    if not isinstance(post.get("slug"), str) or not post["slug"].strip():
        errors.append("slug_missing")
    if not isinstance(post.get("featured_media"), int) or post["featured_media"] <= 0:
        errors.append("featured_image_missing")
    if not str(post.get("title") or "").strip():
        errors.append("title_missing")
    if not str(post.get("content") or "").strip():
        errors.append("content_missing")
    link = post.get("link") or ""
    parsed = urlparse(link)
    if parsed.scheme != "https" or parsed.hostname != expected_site:
        errors.append("invalid_post_link")
    if not isinstance(post.get("id"), int) or post["id"] <= 0:
        errors.append("post_id_missing")
    return Readiness(not errors, tuple(errors))


def require_wordpress_readiness(post: dict, **kwargs) -> None:
    result = validate_wordpress_readiness(post, **kwargs)
    if not result.ready:
        raise ValueError("wordpress_not_ready: " + ", ".join(result.errors))
