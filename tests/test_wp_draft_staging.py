"""Offline regression for a minimal safe RSS-to-WordPress draft writer."""
from unittest.mock import Mock
from mkt_flow_p0.wp_draft_staging import stage_rss_draft

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

def test_create_private_draft_and_confirm_readback():
    client = Mock()
    client.get.side_effect = [
        response(200, []),
        response(200, {"status": "draft",
                       "id": 9752,
                       "slug": "android-recebe-novos-recursos-para-usuarios-brasileiros-"
                               + __import__("hashlib").sha256(SOURCE.encode()).hexdigest()[:12],
                       "link": "https://conexotech.com.br/?p=9752"})
    ]
    client.post.return_value = response(201, {"id": 9752, "status": "draft"})
    result = stage_rss_draft(**BASE, request_client=client)
    assert result["acao"] == "publicado_rascunho"
    assert result["escreveu"] is True and result["post_id"] == 9752
    assert result["revisao_factual"] == "PENDENTE"
    sent = client.post.call_args.kwargs["json"]
    assert sent["status"] == "draft"
    assert sent["comment_status"] == "closed"
    assert "publish" not in str(sent)
    assert client.post.call_count == 1

def test_existing_draft_is_reused_without_updating():
    client = Mock()
    client.get.return_value = response(200, [{"id": 9752, "status": "draft", "link": "link"}])
    result = stage_rss_draft(**BASE, request_client=client)
    assert result["acao"] == "publicado_rascunho"
    assert result["reutilizado"] is True and result["escreveu"] is False
    client.post.assert_not_called()

def test_published_collision_is_never_overwritten():
    client = Mock()
    client.get.return_value = response(200, [{"id": 9752, "status": "publish"}])
    result = stage_rss_draft(**BASE, request_client=client)
    assert result["acao"] == "bloqueado"
    client.post.assert_not_called()

def test_invalid_or_missing_credentials_cannot_write():
    for update in ({"wp_user": ""}, {"wp_url": "https://other.example"},
                   {"source_url": "javascript:alert(1)"}, {"content": "curto"}):
        client = Mock()
        result = stage_rss_draft(**{**BASE, **update}, request_client=client)
        assert result["acao"] == "bloqueado"
        client.get.assert_not_called()
        client.post.assert_not_called()

def test_read_failure_and_timeout_do_not_start_retry_or_publish():
    client = Mock()
    client.get.return_value = response(403, {})
    result = stage_rss_draft(**BASE, request_client=client)
    assert result["acao"] == "falha"
    client.post.assert_not_called()

    import requests
    client = Mock()
    client.get.return_value = response(200, [])
    client.post.side_effect = requests.Timeout("ambiguous timeout")
    result = stage_rss_draft(**BASE, request_client=client)
    assert result["acao"] == "falha"
    assert result["retry_automatic"] is False
    assert client.post.call_count == 1

def test_failed_readback_never_claims_success():
    client = Mock()
    client.get.side_effect = [response(200, []), response(200, {"status": "publish"})]
    client.post.return_value = response(201, {"id": 9752, "status": "draft"})
    result = stage_rss_draft(**BASE, request_client=client)
    assert result["acao"] == "falha"
    assert result["retry_automatic"] is False
    assert result["post_id"] == 9752

def test_staging_is_optional_not_required():
    import hashlib
    client = Mock()
    slug = "android-recebe-novos-recursos-para-usuarios-brasileiros-" + hashlib.sha256(SOURCE.encode()).hexdigest()[:12]
    client.get.side_effect = [
        response(200, []),
        response(200, {"status": "draft", "id": 9763, "slug": slug,
                       "link": "https://staging.conexotech.com.br/?p=9763"})
    ]
    client.post.return_value = response(201, {"id": 9763, "status": "draft"})
    result = stage_rss_draft(**{**BASE, "wp_url": "https://staging.conexotech.com.br"},
                             request_client=client)
    assert result["acao"] == "publicado_rascunho"
    assert result["post_id"] == 9763 and result["status"] == "draft"
    assert result["revisao_factual"] == "PENDENTE"
    assert client.post.call_args.args[0] == "https://staging.conexotech.com.br/wp-json/wp/v2/posts"
    assert client.post.call_args.kwargs["json"]["status"] == "draft"
    assert client.post.call_count == 1


def test_unknown_host_cannot_be_used_even_with_valid_credentials():
    client = Mock()
    result = stage_rss_draft(**{**BASE, "wp_url": "https://other.example"},
                             request_client=client)
    assert result["acao"] == "bloqueado" and result["escreveu"] is False
    client.post.assert_not_called()
    client.get.assert_not_called()
