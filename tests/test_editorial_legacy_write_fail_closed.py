"""Regressão: rascunhos/taxonomia nativos sem liberar publicação editorial.

Chamadas de rede são inteiramente mockadas. Nenhuma escrita real no WordPress.
"""
from unittest.mock import MagicMock, patch

from mkt_flow_p0 import wp_publisher as wp


def _response(status, data):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = data
    return r


def test_new_support_page_stays_draft():
    with patch.object(wp.requests, "get", return_value=_response(200, [])), \
         patch.object(wp.requests, "post", return_value=_response(201, {"id": 7, "link": "x", "status": "draft"})) as post:
        result = wp.publicar_pagina("Página", "<p>texto</p>", "pagina", "https://conexotech.com.br", "u", "p")
    assert result["page_id"] == 7
    assert post.call_args.kwargs["json"]["status"] == "draft"


def test_existing_published_page_is_not_modified():
    with patch.object(wp.requests, "get", return_value=_response(200, [{"id": 8, "status": "publish"}])), \
         patch.object(wp.requests, "post") as post:
        result = wp.publicar_pagina("Página", "<p>texto</p>", "pagina", "https://conexotech.com.br", "u", "p")
    assert "erro" in result
    post.assert_not_called()


def test_terms_use_normal_authenticated_wordpress_permissions():
    with patch.object(wp.requests, "get", return_value=_response(200, [])), \
         patch.object(wp.requests, "post", return_value=_response(201, {"id": 10})) as post:
        assert wp.garantir_categoria("https://conexotech.com.br", "u", "p", "Notícias") == 10
        assert wp.garantir_tag("https://conexotech.com.br", "u", "p", "Tecnologia") == 10
    assert post.call_count == 2


def test_rank_math_direct_post_stays_blocked():
    with patch.object(wp.requests, "post") as post:
        result = wp._aplicar_rank_math("https://conexotech.com.br", "u", "p", 123, {"title": "Teste"})
        assert "bloqueada" in result["meta_aviso"]
        post.assert_not_called()


def test_direct_comparison_mcp_write_is_blocked():
    with patch.object(wp.requests, "post") as post:
        result = wp.executar_ferramenta_mcp(
            "https://conexotech.com.br", "u", "p", "create_comparativo", {"title": "Teste"}
        )
        assert "bloqueado" in result["erro"]
        post.assert_not_called()
