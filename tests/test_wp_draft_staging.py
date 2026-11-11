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


def test_explicit_author_and_seo_excerpt_sent_and_read_back():
    client = Mock()
    post = {**readback(), 'author': 3, 'excerpt': {'raw': 'Descricao SEO revisavel.'}}
    client.get.side_effect = [response(200, []), response(200, []), response(200, post)]
    client.post.return_value = response(201, {'id': 9752, 'status': 'draft'})
    result = mod.stage_rss_draft(**BASE, request_client=client,
                               author_id=3, excerpt='Descricao SEO revisavel.')
    assert result['acao'] == 'publicado_rascunho'
    sent = client.post.call_args.kwargs['json']
    assert sent['author'] == 3 and sent['excerpt'] == 'Descricao SEO revisavel.'


def test_mismatched_author_or_excerpt_is_not_success():
    for author, excerpt in [(4, 'Descricao SEO revisavel.'), (3, 'Outra descricao')]:
        client = Mock()
        post = {**readback(), 'author': author, 'excerpt': {'raw': excerpt}}
        client.get.side_effect = [response(200, []), response(200, []), response(200, post)]
        client.post.return_value = response(201, {'id': 9752, 'status': 'draft'})
        result = mod.stage_rss_draft(**BASE, request_client=client,
                                   author_id=3, excerpt='Descricao SEO revisavel.')
        assert result['acao'] == 'falha' and result['retry_automatic'] is False
        assert client.post.call_count == 1


def test_invalid_metadata_is_rejected_before_network():
    for metadata in [{'author_id': True}, {'author_id': 0}, {'excerpt': ''}, {'excerpt': {}}]:
        client = Mock()
        result = mod.stage_rss_draft(**BASE, request_client=client, **metadata)
        assert result['acao'] == 'bloqueado'
        client.get.assert_not_called()
        client.post.assert_not_called()


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


def test_media_requires_operator_rights_and_valid_id_without_network():
    for fields in (
            {"featured_media_id": 9714},
            {"media_rights_confirmed": True},
            {"featured_media_id": -1, "media_rights_confirmed": True}):
        client = Mock()
        result = mod.stage_rss_draft(**BASE, **fields, request_client=client)
        assert result["acao"] == "bloqueado"
        client.get.assert_not_called()
        client.post.assert_not_called()


def test_existing_authorized_media_is_attached_with_readback():
    client = Mock()
    media = {"id": 9714, "media_type": "image",
             "mime_type": "image/jpeg", "alt_text": "Imagem autorizada do artigo"}
    post = readback()
    post["featured_media"] = 9714
    client.get.side_effect = [response(200, media), response(200, []), response(200, []),
                              response(200, post)]
    client.post.return_value = response(201, {"id": 9752, "status": "draft"})
    result = mod.stage_rss_draft(**BASE, featured_media_id=9714,
                                 media_rights_confirmed=True, request_client=client)
    assert result["acao"] == "publicado_rascunho"
    assert client.post.call_args.kwargs["json"]["featured_media"] == 9714
    assert client.post.call_args.kwargs["json"]["status"] == "draft"


def test_unavailable_or_unlabeled_media_blocks_before_writing():
    for media in (response(404, {}),
                  response(200, {"id": 9714, "media_type": "image",
                                 "mime_type": "image/png", "alt_text": ""}),
                  response(200, {"id": 9714, "media_type": "file",
                                 "mime_type": "application/pdf", "alt_text": "PDF"})):
        client = Mock()
        client.get.return_value = media
        r = mod.stage_rss_draft(**BASE, featured_media_id=9714,
                                media_rights_confirmed=True, request_client=client)
        assert r["acao"] == "bloqueado"
        assert r["motivo"] == "midia_wp_nao_validada"
        client.post.assert_not_called()


def test_existing_draft_with_different_featured_media_is_not_overwritten():
    client = Mock()
    media = {"id": 9714, "media_type": "image",
             "mime_type": "image/jpeg", "alt_text": "Imagem autorizada"}
    old = readback()
    old["featured_media"] = 1234
    client.get.side_effect = [response(200, media), response(200, [old]),
                              response(200, []), response(200, old)]
    r = mod.stage_rss_draft(**BASE, featured_media_id=9714,
                            media_rights_confirmed=True, request_client=client)
    assert r["acao"] == "bloqueado"
    client.post.assert_not_called()
