"""Regressao da ponte ChatGPT-first -> SEO consultivo -> preview e body WP."""
import json
from pathlib import Path

import pytest

from mkt_flow_p0.editorial_core_offline import gerar_corpo_wordpress, gerar_html, processar


def _pacote():
    return {
        "schema_version": "1.0",
        "article_id": "conexo-test-2026",
        "status": "aguardando_revisao",
        "title": "Como funcionam metadados SEO em um artigo do WordPress",
        "seo": {"title": "Como funcionam os metadados SEO no WordPress",
                "description": "Explicacao editorial sobre os metadados da pagina.",
                "slug": "metadados-seo-wordpress", "keyword": "seo wordpress"},
        "sources": [{"name": "WordPress", "url": "https://wordpress.org/"}],
        "claims": [],
        "review": {"approved": False},
        "related_articles": [
            {"title": "Reviews", "url": "https://conexotech.com.br/reviews/"},
        ],
    }


def _texto():
    return "## Contexto\n\n" + (
        "Este paragrafo e uma demonstracao de conteudo editorial sem alegacoes factuais. "
        * 19
    )


def test_preview_noindex_but_wordpress_fragment_has_no_head():
    preview = gerar_html(_pacote(), _texto())
    body = gerar_corpo_wordpress(_pacote(), _texto())
    assert 'content="noindex,nofollow"' in preview
    assert '<title>' in preview
    assert "<html" not in body
    assert "<head" not in body
    assert "noindex" not in body
    assert "<h1>" not in body
    assert "<h2>Fontes</h2>" in body
    assert "<h2>Leia também</h2>" in body


def test_manifest_seo_and_review_still_pending(tmp_path):
    meta = tmp_path / "article.json"
    markdown = tmp_path / "article.md"
    meta.write_text(json.dumps(_pacote(), ensure_ascii=False), encoding="utf-8")
    markdown.write_text(_texto(), encoding="utf-8")
    manifest = processar(meta, markdown, tmp_path / "output")
    assert manifest["wordpress_written"] is False
    assert manifest["status"] == "aguardando_revisao"
    assert manifest["factual_review"] == "NAO_VERIFICADO"
    assert "seo_preflight" in manifest
    assert "menos_de_tres_links_internos" in manifest["seo_preflight"]["avisos"]
    assert Path(manifest["html"]).is_file()
    assert Path(manifest["wordpress_body"]).is_file()
    assert "noindex" not in Path(manifest["wordpress_body"]).read_text(encoding="utf-8")
    saved = tmp_path / "output" / "metadados-seo-wordpress.report.json"
    assert json.loads(saved.read_text(encoding="utf-8"))["content_sha256"] == manifest["content_sha256"]


def test_revision_changes_fingerprint(tmp_path):
    meta = tmp_path / "article.json"
    markdown = tmp_path / "article.md"
    meta.write_text(json.dumps(_pacote(), ensure_ascii=False), encoding="utf-8")
    markdown.write_text(_texto(), encoding="utf-8")
    first = processar(meta, markdown, tmp_path / "output")["content_sha256"]
    markdown.write_text(_texto() + "\nNovo paragrafo revisado.", encoding="utf-8")
    second = processar(meta, markdown, tmp_path / "output")["content_sha256"]
    assert first != second


def test_nunca_renderiza_aprovacao_autodeclarada():
    packet = _pacote()
    packet["review"]["approved"] = True
    with pytest.raises(ValueError):
        gerar_corpo_wordpress(packet, _texto())


def test_links_maliciosos_nao_chegam_ao_wordpress():
    with pytest.raises(ValueError):
        gerar_corpo_wordpress(_pacote(), _texto() + "\n[link](javascript:alert)")
