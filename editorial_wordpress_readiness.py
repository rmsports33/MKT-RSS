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
    if type(expected_category_id) is not int or expected_category_id <= 0:
        errors.append("invalid_category_configuration")
    if post.get("status") not in ("draft", "pending", "future"):
        errors.append("unexpected_status")
    categories = post.get("categories")
    if not isinstance(categories, list) or any(type(c) is not int or c <= 0 for c in categories):
        categories = []
        errors.append("invalid_categories")
    if expected_category_id not in categories:
        errors.append("news_category_missing")
    if 1 in categories:
        errors.append("uncategorized_present")
    if not isinstance(post.get("slug"), str) or not post["slug"].strip():
        errors.append("slug_missing")
    if type(post.get("featured_media")) is not int or post["featured_media"] <= 0:
        errors.append("featured_image_missing")
    if not isinstance(post.get("title"), str) or not post["title"].strip():
        errors.append("title_missing")
    if not isinstance(post.get("content"), str) or not post["content"].strip():
        errors.append("content_missing")
    link = post.get("link")
    try:
        parsed = urlparse(link) if isinstance(link, str) else None
        valid_link = parsed and parsed.scheme == "https" and parsed.hostname == expected_site and not parsed.username and not parsed.password and parsed.port in (None, 443)
    except ValueError:
        valid_link = False
    if not valid_link:
        errors.append("invalid_post_link")
    if type(post.get("id")) is not int or post["id"] <= 0:
        errors.append("post_id_missing")
    return Readiness(not errors, tuple(errors))


def require_wordpress_readiness(post: dict, **kwargs) -> None:
    result = validate_wordpress_readiness(post, **kwargs)
    if not result.ready:
        raise ValueError("wordpress_not_ready: " + ", ".join(result.errors))

