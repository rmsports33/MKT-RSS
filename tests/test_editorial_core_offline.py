"""Teste offline do contrato editorial ChatGPT-first, sem chamadas externas."""
import json
import pytest

from mkt_flow_p0.editorial_core_offline import gerar_html, processar, validar_pacote


def artigo():
    return {
        "schema_version": "1.0", "article_id": "cx-test-001",
        "status": "aguardando_revisao", "title": "Notícia em revisão",
        "seo": {"title": "Notícia tecnológica em revisão", "description": "Resumo de conteúdo para testes offline.",
                "slug": "noticia-em-revisao", "keyword": "tecnologia"},
        "sources": [{"name": "Fonte oficial", "url": "https://www.python.org/"}],
        "claims": [], "review": {"approved": False},
        "related_articles": [{"title": "Outra pauta", "url": "https://conexotech.com.br/noticias/"}],
    }


def corpo():
    return "## Entenda\n\n" + ("Este texto é apenas uma demonstração técnica sem alegações factuais. " * 18)


def test_gera_html_noindex_e_fontes():
    output = gerar_html(artigo(), corpo())
    assert 'name="robots" content="noindex,nofollow"' in output
    assert "<h1>Notícia em revisão</h1>" in output
    assert "https://www.python.org/" in output
    assert "Leia também" in output


def test_bloqueia_link_inseguro():
    with pytest.raises(ValueError, match="HTTPS"):
        gerar_html(artigo(), corpo() + "\n[clique](javascript:alert)")


def test_bloqueia_ausencia_fontes():
    a = artigo()
    a["sources"] = []
    assert "Fontes HTTPS obrigatorias" in validar_pacote(a, corpo())


def test_bloqueia_pacote_preaprovado():
    a = artigo()
    a["review"]["approved"] = True
    assert validar_pacote(a, corpo())


def test_bloqueia_slug_path_traversal():
    a = artigo()
    a["seo"]["slug"] = "../../malicioso"
    assert "Slug invalido" in validar_pacote(a, corpo())


def test_escreve_html_e_relatorio_local(tmp_path):
    metadata = tmp_path / "artigo.json"
    md = tmp_path / "artigo.md"
    metadata.write_text(json.dumps(artigo(), ensure_ascii=False), encoding="utf-8")
    md.write_text(corpo(), encoding="utf-8")
    result = processar(metadata, md, tmp_path / "outputs")
    assert result["wordpress_written"] is False
    assert (tmp_path / "outputs" / "noticia-em-revisao.html").is_file()
    assert (tmp_path / "outputs" / "noticia-em-revisao.report.json").is_file()


def test_html_bruto_rejeitado():
    with pytest.raises(ValueError, match="HTML bruto"):
        gerar_html(artigo(), corpo() + "\n<div onclick='x'>Inseguro</div>")


def test_contrato_canonico_invalido_bloqueado():
    a = artigo()
    a["contrato_editorial"] = {"contract_version": "0.9", "content_type": "noticia", "sources": [], "claims": []}
    assert "Contrato editorial canonico invalido" in validar_pacote(a, corpo())


def test_contrato_ausente_nao_concede_aprovacao(tmp_path):
    metadata = tmp_path / "artigo.json"
    md = tmp_path / "artigo.md"
    metadata.write_text(json.dumps(artigo(), ensure_ascii=False), encoding="utf-8")
    md.write_text(corpo(), encoding="utf-8")
    result = processar(metadata, md, tmp_path / "outputs")
    assert result["aprovacao_publicacao"] is False
    assert result["contrato_editorial"]["veredito"] == "BLOQUEADO"


def test_claim_localizada_com_link_markdown_na_frase(tmp_path):
    a = artigo()
    a["claims"] = [{"id": "cl1", "text": "Google lançou Android hoje.", "evidence_ids": []}]
    md = corpo() + "\n\nGoogle lançou [Android](https://www.python.org/) hoje.\n"
    metadata = tmp_path / "a.json"
    body = tmp_path / "a.md"
    metadata.write_text(json.dumps(a, ensure_ascii=False), encoding="utf-8")
    body.write_text(md, encoding="utf-8")
    result = processar(metadata, body, tmp_path / "out")
    assert result["rastreabilidade_claims"][0]["texto_localizado"] is True
    assert result["rastreabilidade_claims"][0]["evidencia_aprovada"] is False
    assert result["aprovacao_publicacao"] is False
