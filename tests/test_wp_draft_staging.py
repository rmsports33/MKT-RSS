"""Fail-closed WordPress draft publisher: source idempotency, version readback, no publication."""
from unittest.mock import Mock
import requests

from mkt_flow_p0 import wp_draft_staging as mod

SOURCE = "https://example.org/tecnologia/noticia"
TITLE = "Android recebe novos recursos para usuários brasileiros"
CONTENT = "<p>" + ("Texto editorial para revisão sem aprovação factual automática. " * 5) + "</p>"
BASE = {"title": TITLE, "content": CONTENT, "source_url": SOURCE,
        "wp_url": "https://conexotech.com.br", "wp_user": "user",
        "wp_password": "synthetic-private-password"}


def response(status, data):
    r = Mock()
    r.status_code = status
    r.json.return_value = data
    return r


def readback(pid=9752, status="draft", slug=None, content=CONTENT, title=TITLE):
    return {"id": pid, "status": status, "slug": slug or mod._slug(TITLE, SOURCE),
            "content": {"raw": content}, "title": {"raw": title},
            "link": "https://conexotech.com.br/?p=" + str(pid)}


def test_create_private_draft_and_confirm_content_readback():
    client = Mock()
    client.get.side_effect = [response(200, []), response(200, []),
                              response(200, readback())]
    client.post.return_value = response(201, {"id": 9752, "status": "draft"})
    result = mod.stage_rss_draft(**BASE, request_client=client)
    assert result["acao"] == "publicado_rascunho"
    assert result["escreveu"] is True and result["post_id"] == 9752
    assert result["revisao_factual"] == "PENDENTE"
    sent = client.post.call_args.kwargs["json"]
    assert sent["status"] == "draft" and sent["comment_status"] == "closed"
    assert "publish" not in str(sent)
    assert client.post.call_count == 1
    for call in client.get.call_args_list[:2]:
        assert "draft" in call.kwargs["params"]["status"]
        assert call.kwargs["params"]["context"] == "edit"


def test_existing_matching_draft_is_reused_without_updating():
    client = Mock()
    post = readback()
    client.get.side_effect = [response(200, [post]), response(200, []),
                              response(200, post)]
    result = mod.stage_rss_draft(**BASE, request_client=client)
    assert result["acao"] == "publicado_rascunho"
    assert result["reutilizado"] is True and result["escreveu"] is False
    client.post.assert_not_called()


def test_existing_legacy_title_slug_is_reused_if_version_matches():
    client = Mock()
    post = readback(slug=mod._legacy_slug(TITLE, SOURCE))
    client.get.side_effect = [response(200, []), response(200, [post]),
                              response(200, post)]
    result = mod.stage_rss_draft(**BASE, request_client=client)
    assert result["acao"] == "publicado_rascunho"
    assert result["reutilizado"] is True
    client.post.assert_not_called()


def test_title_rewrite_cannot_create_different_source_slug():
    assert mod._slug(TITLE, SOURCE) == mod._slug(
        "Outro título gerado pela inteligência artificial", SOURCE)


def test_existing_stale_draft_is_blocked_not_reused():
    client = Mock()
    post = readback(content="<p>ARTIGO ANTIGO</p>")
    client.get.side_effect = [response(200, [post]), response(200, []),
                              response(200, post)]
    result = mod.stage_rss_draft(**BASE, request_client=client)
    assert result["acao"] == "bloqueado"
    assert result["motivo"] == "versao_rascunho_divergente"
    assert result["retry_automatic"] is False
    client.post.assert_not_called()


def test_readback_truncation_never_claims_success():
    client = Mock()
    client.get.side_effect = [response(200, []), response(200, []),
                              response(200, readback(content="<p>TRUNCADO</p>"))]
    client.post.return_value = response(201, {"id": 9752, "status": "draft"})
    result = mod.stage_rss_draft(**BASE, request_client=client)
    assert result["acao"] == "falha"
    assert result["post_id"] == 9752 and result["escreveu"] is True
    assert result["retry_automatic"] is False


def test_published_collision_is_never_overwritten():
    client = Mock()
    post = readback(status="publish")
    client.get.side_effect = [response(200, [post]), response(200, []),
                              response(200, post)]
    result = mod.stage_rss_draft(**BASE, request_client=client)
    assert result["acao"] == "bloqueado"
    client.post.assert_not_called()


def test_two_posts_matching_source_are_never_overwritten():
    client = Mock()
    client.get.side_effect = [response(200, [readback(pid=11)]),
                              response(200, [readback(pid=12)])]
    result = mod.stage_rss_draft(**BASE, request_client=client)
    assert result["acao"] == "bloqueado"
    client.post.assert_not_called()


def test_invalid_credentials_site_source_or_content_cannot_write():
    for change in ({"wp_user": ""}, {"wp_url": "https://other.example"},
                   {"source_url": "javascript:alert(1)"}, {"content": "curto"}):
        client = Mock()
        result = mod.stage_rss_draft(**{**BASE, **change}, request_client=client)
        assert result["acao"] == "bloqueado"
        client.get.assert_not_called()
        client.post.assert_not_called()


def test_listing_error_does_not_create():
    client = Mock()
    client.get.return_value = response(403, {})
    result = mod.stage_rss_draft(**BASE, request_client=client)
    assert result["acao"] == "falha"
    client.post.assert_not_called()


def test_ambiguous_timeout_never_automatically_retries():
    client = Mock()
    client.get.side_effect = [response(200, []), response(200, [])]
    client.post.side_effect = requests.Timeout("ambiguous")
    result = mod.stage_rss_draft(**BASE, request_client=client)
    assert result["acao"] == "falha"
    assert result["retry_automatic"] is False
    assert client.post.call_count == 1


def test_malformed_201_response_marks_write_uncertain():
    client = Mock()
    client.get.side_effect = [response(200, []), response(200, [])]
    client.post.return_value = response(201, {"id": "9752", "status": "draft"})
    result = mod.stage_rss_draft(**BASE, request_client=client)
    assert result["acao"] == "falha"
    assert result["escrita_indeterminada"] is True
    assert result["retry_automatic"] is False


def test_staging_optional_and_never_publish():
    client = Mock()
    client.get.side_effect = [response(200, []), response(200, []),
                              response(200, readback())]
    client.post.return_value = response(201, {"id": 9752, "status": "draft"})
    result = mod.stage_rss_draft(
        **{**BASE, "wp_url": "https://staging.conexotech.com.br"},
        request_client=client)
    assert result["acao"] == "publicado_rascunho"
    assert client.post.call_args.args[0] == "https://staging.conexotech.com.br/wp-json/wp/v2/posts"
    assert client.post.call_args.kwargs["json"]["status"] == "draft"
