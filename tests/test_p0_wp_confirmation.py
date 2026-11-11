"""Regressões P0 de confirmação WordPress, totalmente isoladas.

Os xfails representam comportamento incorreto conhecido; não contam como
correção. Mocks impedem chamadas externas, gravações em WP ou Turso.
"""
from unittest.mock import Mock

import pytest

import pipeline_rss
from mkt_flow_p0 import content_filter, extractor, rewriter, image_handler, format as format_module
from mkt_flow_p0 import seo, wp_publisher


@pytest.fixture
def fluxo_isolado(monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline_rss, "DB_PATH", tmp_path / "rss_runs.sqlite")
    monkeypatch.setattr(content_filter, "filtrar_por_tema", lambda *a, **k: {"veredito": "PASS"})
    monkeypatch.setattr(content_filter, "filtrar_item_rss", lambda *a, **k: {"veredito": "PASS"})
    monkeypatch.setattr(content_filter, "filtrar_conteudo", lambda *a, **k: {"veredito": "PASS"})
    monkeypatch.setattr(
        extractor,
        "extrair_conteudo",
        lambda *a, **k: {
            "titulo": "Produto tecnológico fictício",
            "texto": "Texto fictício suficiente para o teste",
            "palavras": 120,
            "qualidade_ok": True,
            "imagem": "",
        },
    )
    monkeypatch.setattr(seo, "enriquecer_com_keywords", lambda *a, **k: [])
    monkeypatch.setattr(
        rewriter,
        "reescrever_materia",
        lambda *a, **k: {
            "titulo_seo": "Produto tecnológico fictício",
            "texto_markdown": "Conteúdo fictício",
            "palavras": 120,
            "tags": [],
            "slug": "produto-ficticio",
            "meta_description": "Resumo fictício",
        },
    )
    monkeypatch.setattr(rewriter, "adicionar_atribuicao", lambda texto, *a: texto)
    monkeypatch.setattr(format_module, "markdown_para_html", lambda texto: "<p>Teste</p>")
    monkeypatch.setattr(format_module, "sanitizar_url", lambda url: url)
    monkeypatch.setattr(image_handler, "preparar_capa", lambda *a, **k: {})
    monkeypatch.setattr(wp_publisher, "garantir_categoria", lambda *a, **k: None)
    monkeypatch.setattr(wp_publisher, "garantir_tag", lambda *a, **k: None)
    monkeypatch.setenv("WP_URL", "https://example.invalid")
    monkeypatch.setenv("WP_USER", "usuario-ficticio")
    monkeypatch.setenv("WP_APP_PASSWORD", "senha-ficticia-nao-real")
    return {"titulo": "Produto tecnológico fictício", "resumo": "Teste", "link": "https://example.invalid/noticia", "fonte": "fixture"}


@pytest.mark.xfail(strict=True, reason="P0: ausência de post_id é reportada como publicado_rascunho")
@pytest.mark.parametrize("resposta", [
    {"erro": "HTTP 401"},
    {"erro": "HTTP 500"},
    {"aviso": "sem post_id"},
])
def test_wp_sem_confirmacao_nao_pode_contar_sucesso(fluxo_isolado, monkeypatch, resposta):
    monkeypatch.setattr(wp_publisher, "publicar_no_wordpress", lambda *a, **k: resposta)
    resultado = pipeline_rss.processar_item(fluxo_isolado)
    assert resultado["acao"] == "falha"
    assert not resultado.get("wp", {}).get("post_id")


def test_wp_com_post_id_retorna_sucesso(fluxo_isolado, monkeypatch):
    monkeypatch.setattr(
        wp_publisher,
        "publicar_no_wordpress",
        lambda *a, **k: {"post_id": 123, "status": "draft", "link": "https://example.invalid/?p=123"},
    )
    resultado = pipeline_rss.processar_item(fluxo_isolado)
    assert resultado["acao"] == "publicado_rascunho"
    assert resultado["wp"]["post_id"] == 123
