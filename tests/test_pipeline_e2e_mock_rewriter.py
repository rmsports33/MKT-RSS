"""Full RSS pipeline test with an injected rewriter, no network or WordPress."""
from unittest.mock import Mock
import pipeline_rss
from mkt_flow_p0 import content_filter, extractor, rewriter, seo, format as fmt
from test_post_ai_claim_coverage import dados


def test_mocked_rewriter_propagates_claims_and_never_calls_wp(monkeypatch):
    contract, captures = dados()
    generated = "The product got an update."
    events = []
    fake_wp = Mock(side_effect=AssertionError("WordPress must not be invoked"))
    # If any WordPress module is imported, the test must fail rather than fake success.
    import builtins
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.startswith("mkt_flow_p0.wordpress") or name.startswith("wordpress"):
            fake_wp()
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(content_filter, "filtrar_por_tema", lambda *a: {"veredito": "APROVADO"})
    monkeypatch.setattr(content_filter, "filtrar_item_rss", lambda *a: {"veredito": "APROVADO"})
    monkeypatch.setattr(content_filter, "filtrar_conteudo", lambda *a: {"veredito": "APROVADO"})
    monkeypatch.setattr(extractor, "extrair_conteudo", lambda *a: {
        "titulo": "Atualização Android", "texto": "Anúncio: O produto recebeu uma atualização.",
        "palavras": 100, "qualidade_ok": True, "imagem": ""})
    monkeypatch.setattr(seo, "enriquecer_com_keywords", lambda *a, **kw: [])
    monkeypatch.setattr(fmt, "markdown_para_html", lambda *a: "<p>prévia</p>")
    monkeypatch.setattr(rewriter, "adicionar_atribuicao", lambda texto, *a: texto)

    def injected_rewriter(*args, **kwargs):
        events.append("redator")
        return {
            "texto_markdown": generated, "titulo_seo": "Teste",
            "contrato_editorial": contract,
            "referencias_traducao": {"the product got an update.": ["c1"]},
        }

    monkeypatch.setattr(rewriter, "reescrever_materia", injected_rewriter)
    monkeypatch.delenv("GATE_PUBLICACAO_ENABLED", raising=False)
    result = pipeline_rss.processar_item({
        "titulo": "Atualização Android", "resumo": "Anúncio", "link": "https://example.org/source",
        "fonte": "Fonte Exemplo",
    }, capturas_aprovadas=captures)
    assert events == ["redator"]
    assert result["auditoria_cobertura"]["veredito"] == "REVISAO_SEMANTICA_PENDENTE"
    assert result["auditoria_cobertura"]["sem_referencia"] == 0
    assert result["acao"] == "bloqueado"
    assert result["escreveu"] is False
    assert result["verificacao_factual"] == "NAO_VERIFICADO"
    fake_wp.assert_not_called()


def test_no_mapping_from_mocked_rewriter_stays_blocked(monkeypatch):
    contract, captures = dados()
    monkeypatch.setattr(content_filter, "filtrar_por_tema", lambda *a: {"veredito": "APROVADO"})
    monkeypatch.setattr(content_filter, "filtrar_item_rss", lambda *a: {"veredito": "APROVADO"})
    monkeypatch.setattr(content_filter, "filtrar_conteudo", lambda *a: {"veredito": "APROVADO"})
    monkeypatch.setattr(extractor, "extrair_conteudo", lambda *a: {
        "titulo": "Atualização", "texto": "Anúncio: O produto recebeu uma atualização.",
        "palavras": 100, "qualidade_ok": True, "imagem": ""})
    monkeypatch.setattr(seo, "enriquecer_com_keywords", lambda *a, **kw: [])
    monkeypatch.setattr(fmt, "markdown_para_html", lambda *a: "<p>texto</p>")
    monkeypatch.setattr(rewriter, "adicionar_atribuicao", lambda texto, *a: texto)
    monkeypatch.setattr(rewriter, "reescrever_materia", lambda *a, **k: {
        "texto_markdown": "The product got an update.",
        "titulo_seo": "Teste", "contrato_editorial": contract,
    })
    monkeypatch.delenv("GATE_PUBLICACAO_ENABLED", raising=False)
    result = pipeline_rss.processar_item({
        "titulo": "Atualização Android", "resumo": "Anúncio",
        "link": "https://example.org/source", "fonte": "Fonte",
    }, capturas_aprovadas=captures)
    assert result["auditoria_cobertura"]["veredito"] == "BLOQUEADO"
    assert result["acao"] == "bloqueado" and result["escreveu"] is False
