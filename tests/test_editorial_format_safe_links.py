"""Test HTML-safe Markdown links without network or WordPress."""
import pytest
from mkt_flow_p0.format import markdown_para_html


@pytest.mark.parametrize("url", [
    "javascript:alert", "data:text/html,hello", "vbscript:msg",
    "file:///etc/passwd", "http://example.org", "//example.org",
    "https://user:password@example.org/path", "https://example.org:8080/path",
    "https://bad", "https://[unclosed",
])
def test_unsafe_href_cannot_become_active_html(url):
    result = markdown_para_html("[Fonte](" + url + ")")
    assert "<a " not in result
    assert "Fonte" in result


def test_https_link_keeps_target_and_rel():
    result = markdown_para_html("[AppFunctions](https://developer.android.com/ai/appfunctions)")
    assert 'href="https://developer.android.com/ai/appfunctions"' in result
    assert 'rel="noopener noreferrer"' in result


def test_query_string_is_html_escaped_exactly_once():
    result = markdown_para_html("[Fonte](https://example.org/news?x=1&y=2)")
    assert "x=1&amp;y=2" in result
    assert "&amp;amp;" not in result


def test_link_label_escapes_inline_html():
    result = markdown_para_html("[<svg onload=x>](https://example.org/news)")
    assert "<svg" not in result
    assert "&lt;svg" in result


def test_url_controls_and_credentials_cannot_bypass_guard():
    result = markdown_para_html("[Teste](https://user:pw@example.org/a)")
    assert "<a " not in result
