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


def validate_complete_editorial_draft(post: dict, *, expected_category_id: int = 10,
                                      expected_site: str = "conexotech.com.br") -> Readiness:
    """Strict readback contract for marking a saved WordPress draft ready for owner review.

    Never generates approvals, makes network calls, or changes WordPress status.
    Missing information is a concrete correction task, not an assumed PASS.
    """
    import re
    from html import unescape

    base = validate_wordpress_readiness(
        post, expected_category_id=expected_category_id, expected_site=expected_site)
    errors = list(base.errors)
    if not isinstance(post, dict):
        return Readiness(False, tuple(errors))
    title = post.get("title")
    content = post.get("content")
    excerpt = post.get("excerpt")
    plain = re.sub(r"<[^>]*>", " ", content) if isinstance(content, str) else ""
    plain = unescape(plain)
    if not isinstance(title, str) or len(title.strip()) < 15:
        errors.append("title_incomplete")
    if len(plain.strip()) < 1000:
        errors.append("article_incomplete")
    if not isinstance(excerpt, str) or len(unescape(re.sub(r"<[^>]*>", " ", excerpt)).strip()) < 60:
        errors.append("seo_excerpt_missing_or_short")
    credit = post.get("image_caption")
    if not isinstance(credit, str) or len(credit.strip()) < 12:
        errors.append("image_credit_missing")
    urls = re.findall(r"https?://[^\s\"'<>]+", content or "") if isinstance(content, str) else []
    from urllib.parse import urlparse
    external = [u for u in urls if urlparse(u).hostname not in (expected_site, "www."+expected_site)]
    internal = [u for u in urls if urlparse(u).hostname in (expected_site, "www."+expected_site)]
    if not external:
        errors.append("external_sources_missing")
    # Internal links are editorial recommendations, not delivery blockers.
    # Never manufacture a link or demand an exception for its absence.
    return Readiness(not errors, tuple(dict.fromkeys(errors)))


def require_complete_editorial_draft(post: dict, **kwargs) -> None:
    result = validate_complete_editorial_draft(post, **kwargs)
    if not result.ready:
        raise ValueError("editorial_draft_incomplete: " + ", ".join(result.errors))
