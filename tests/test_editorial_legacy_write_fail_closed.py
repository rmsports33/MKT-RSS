"""Regression: legacy WordPress writers may not bypass the signed editorial gate.

No network, credentials, WordPress changes or paid runners required.
"""
from unittest.mock import patch

from mkt_flow_p0 import wp_publisher as wp


def test_page_writer_fails_closed_before_network():
    with patch.object(wp.requests, "get") as get, patch.object(wp.requests, "post") as post:
        result = wp.publicar_pagina("Página", "<p>texto</p>", "pagina", "https://conexotech.com.br", "u", "p")
        assert "gate editorial" in result["erro"]
        get.assert_not_called()
        post.assert_not_called()


def test_legacy_term_creation_fails_closed_before_network():
    with patch.object(wp.requests, "get") as get, patch.object(wp.requests, "post") as post:
        assert wp.garantir_categoria("https://conexotech.com.br", "u", "p", "Notícias") is None
        assert wp.garantir_tag("https://conexotech.com.br", "u", "p", "Tecnologia") is None
        get.assert_not_called()
        post.assert_not_called()


def test_rank_math_legacy_meta_fails_closed_before_network():
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
