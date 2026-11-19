"""Live-source boundary test: real HTTP extraction, deterministic downstream, no WP writing.

This is NOT an end-to-end live LLM test or factual certification.
Requires internet connectivity and existing dependencies. Fails, rather than skips,
when the primary source cannot be extracted.
"""
import os
from unittest.mock import patch
import pytest

from mkt_flow_p0.extractor import extrair_conteudo

SOURCE_URL = "https://blog.google/products-and-platforms/platforms/android/android-drop-september-2026/"

@pytest.mark.skipif(os.getenv('CONEXO_LIVE_SOURCE_TEST') != '1', reason='Live HTTP opt-in: set CONEXO_LIVE_SOURCE_TEST=1')
def test_real_primary_source_extraction_and_failclosed():
    # Real external source fetch performed by the repository's existing extractor.
    captured = extrair_conteudo(SOURCE_URL)
    assert "erro" not in captured, captured.get("erro")
    assert captured.get("qualidade_ok"), {
        "palavras": captured.get("palavras"), "limite": "minimo do extractor"
    }
    assert captured.get("origem") == "trafilatura"
    assert captured.get("texto") and captured.get("palavras", 0) >= 400

    import pipeline_rss
    from mkt_flow_p0 import extractor, rewriter, seo

    def deterministic_rewrite(titulo, texto, **kwargs):
        # Fixed, strictly limited output: no LLM, no hallucinated specs/prices.
        return {
            "titulo_seo": titulo or "Atualizacao do Android",
            "texto_markdown": texto,
            "uso_tokens": {"total": 0},
            "custo_usd_estimado": 0,
        }

    item = {
        "titulo": "Google divulga atualizacao do Android em setembro",
        "resumo": "Atualizacao Android anunciada no blog oficial Google",
        "fonte": "Google Blog",
        "link": SOURCE_URL,
    }
    # Refuse all WP sockets even if a future change accidentally tries to write.
    # Patch outbound socket connection only AFTER the intentional live capture.
    import socket
    def forbidden(*args, **kwargs):
        raise AssertionError("Outbound network forbidden after source capture")

    with patch.object(extractor, "extrair_conteudo", return_value=captured), \
         patch.object(rewriter, "reescrever_materia", side_effect=deterministic_rewrite), \
         patch.object(seo, "enriquecer_com_keywords", return_value=[]), \
         patch.object(socket.socket, "connect", side_effect=forbidden), \
         patch.object(socket.socket, "connect_ex", side_effect=forbidden):
        result = pipeline_rss.processar_item(item, dry_run=False)

    assert result.get("acao") == "bloqueado", result
    # If processing reached post-IA, require explicit factual non-certification.
    if "verificacao_factual" in result:
        assert result["verificacao_factual"] == "NAO_VERIFICADO"
        assert result["escreveu"] is False
