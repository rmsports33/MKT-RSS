from editorial_wordpress_readiness import validate_wordpress_readiness, require_wordpress_readiness
import pytest

BASE = dict(id=9744, status="draft", categories=[10], slug="binance-ataque",
            featured_media=9746, title="Notícia", content="<p>Texto</p>",
            link="https://conexotech.com.br/?p=9744")


def test_valid_draft():
    assert validate_wordpress_readiness(BASE).ready


@pytest.mark.parametrize("change,error", [
    ({"categories": [1]}, "news_category_missing"),
    ({"categories": [10, 1]}, "uncategorized_present"),
    ({"slug": ""}, "slug_missing"),
    ({"featured_media": 0}, "featured_image_missing"),
    ({"featured_media": None}, "featured_image_missing"),
    ({"title": ""}, "title_missing"),
    ({"content": ""}, "content_missing"),
    ({"link": "http://conexotech.com.br/x"}, "invalid_post_link"),
    ({"link": "https://evil.example/x"}, "invalid_post_link"),
    ({"status": "publish"}, "unexpected_status"),
    ({"id": None}, "post_id_missing"),
])
def test_blocks_incomplete(change, error):
    post = {**BASE, **change}
    result = validate_wordpress_readiness(post)
    assert not result.ready
    assert error in result.errors
    with pytest.raises(ValueError):
        require_wordpress_readiness(post)


def test_missing_post_fails_closed():
    assert not validate_wordpress_readiness(None).ready


@pytest.mark.parametrize("change,error", [
    ({"categories": 10}, "news_category_missing"),
    ({"categories": {"10": True}}, "news_category_missing"),
    ({"link": 123}, "invalid_post_link"),
    ({"featured_media": True}, "featured_image_missing"),
    ({"id": True}, "post_id_missing"),
])
def test_malformed_data_fails_closed_without_exception(change, error):
    result = validate_wordpress_readiness({**BASE, **change})
    assert not result.ready
    assert error in result.errors
