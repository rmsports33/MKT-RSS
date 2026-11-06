"""Verifica o caminho RSS -> handoff sem permitir escrita em WordPress.

Testes offline: substitui conectores externos por stubs, nunca usa Groq/rede.
"""
import sys
from types import SimpleNamespace

import pytest

import pipeline_rss
import mkt_flow_p0
from mkt_flow_p0.editorial_identity import criar_handoff_chatgpt


URL = "https://example.org/noticia-android"
ARTICLE = {
    "titulo_seo": "Android ganha novas integrações",
    "slug": "android-integracoes",
    "meta_description": "Análise dos recursos do Android com fontes verificáveis.",
    "texto_markdown": "## Android\n\n" + ("Contexto útil e sustentado por fontes para o leitor brasileiro. " * 20),
}


def _stub(monkeypatch, name, **attrs):
    # Preserve BOTH Python import caches: sys.modules and the package attribute.
    # Otherwise a fake extractor can leak into later tests after monkeypatch undo.
    replacement = SimpleNamespace(**attrs)
    monkeypatch.setitem(sys.modules, "mkt_flow_p0." + name, replacement)
    monkeypatch.setattr(mkt_flow_p0, name, replacement, raising=False)


def _dependencies(monkeypatch, *, invalid_handoff=False):
    calls = []
    handoff = criar_handoff_chatgpt(ARTICLE, url_fonte=URL,
                                   fonte_nome="Fonte original")
    if invalid_handoff:
        handoff["version_sha256"] = "f" * 64

    def wp_write(**kwargs):
        calls.append(kwargs)
        return {"acao": "publicado_rascunho", "post_id": 999, "status": "draft",
                "escreveu": True}

    def rewrite(*args, **kwargs):
        return {**ARTICLE, "editorial_handoff": handoff,
                "contrato_editorial": None, "referencias_traducao": {}}

    allowed = lambda *args, **kwargs: {"veredito": "APROVADO"}
    _stub(monkeypatch, "content_filter", filtrar_por_tema=allowed,
          filtrar_item_rss=allowed, filtrar_conteudo=allowed)
    _stub(monkeypatch, "extractor", extrair_conteudo=lambda _: {
        "titulo": "Android e agentes", "texto": "Texto apurado " * 170,
        "qualidade_ok": True, "palavras": 340, "imagem": ""})
    _stub(monkeypatch, "rewriter", reescrever_materia=rewrite,
          adicionar_atribuicao=lambda text, name, url: text)
    _stub(monkeypatch, "image_handler", preparar_capa=lambda *a, **kw: {"erro": "sem imagem"})
    _stub(monkeypatch, "format", markdown_para_html=lambda text: "<p>Texto</p>",
          sanitizar_url=lambda url: url)
    _stub(monkeypatch, "seo", enriquecer_com_keywords=lambda *a, **kw: [])
    _stub(monkeypatch, "gate_editorial_pos_ia", validar_saida=lambda *a, **kw: {"veredito": "SEM_ALERTAS"})
    _stub(monkeypatch, "adaptador_contrato_editorial",
          avaliar_snapshot_editorial=lambda *a, **kw: {"veredito": "BLOQUEADO"})
    _stub(monkeypatch, "lastro_offline_noticia",
          auditar_lastro_offline=lambda *a, **kw: {"veredito": "BLOQUEADO"})
    _stub(monkeypatch, "auditoria_cobertura_pos_ia",
          auditar_cobertura_pos_ia=lambda *a, **kw: {"veredito": "BLOQUEADO"})
    _stub(monkeypatch, "wp_draft_staging", stage_rss_draft=wp_write)
    monkeypatch.setattr(pipeline_rss, "gate_publicacao_ativo", lambda: False)
    return calls


def test_handoff_only_does_not_write_wp_even_when_flag_enabled(monkeypatch):
    calls = _dependencies(monkeypatch)
    monkeypatch.setenv("CONEXO_RSS_DRAFT", "1")
    out = pipeline_rss.processar_item(
        {"titulo": "Android e agentes", "resumo": "Pesquisa", "link": URL, "fonte": "Oficial"},
        handoff_only=True)
    assert out["acao"] == "pacote_editorial_criado"
    assert out["escreveu"] is False
    assert out["editorial_handoff"]["review_status"] == "PENDING_HUMAN_REVIEW"
    assert calls == []


def test_invalid_handoff_is_blocked_before_write(monkeypatch):
    calls = _dependencies(monkeypatch, invalid_handoff=True)
    monkeypatch.setenv("CONEXO_RSS_DRAFT", "1")
    out = pipeline_rss.processar_item(
        {"titulo": "Android e agentes", "resumo": "Pesquisa", "link": URL},
        handoff_only=True)
    assert out["acao"] == "falha"
    assert out["motivo"] == "handoff_editorial_invalido"
    assert not out["escreveu"]
    assert calls == []


def test_legacy_explicit_draft_mode_remains_available(monkeypatch):
    calls = _dependencies(monkeypatch)
    monkeypatch.setenv("CONEXO_RSS_DRAFT", "1")
    out = pipeline_rss.processar_item(
        {"titulo": "Android e agentes", "resumo": "Pesquisa", "link": URL},
        handoff_only=False)
    assert out["acao"] == "publicado_rascunho"
    assert out["status"] == "draft"
    assert len(calls) == 1


@pytest.mark.parametrize("arguments", [
    ["--handoff-only"],
    ["--handoff-only", "--handoff-dir", "/tmp/test", "--limit", "1"],
    ["--handoff-only", "--handoff-dir", "/tmp/test", "--fonte", "tecnoblog"],
    ["--handoff-only", "--handoff-dir", "/tmp/test", "--dry-run"],
    ["--handoff-only", "--handoff-dir", "/tmp/test", "--queue-only"],
    ["--handoff-only", "--handoff-dir", "/tmp/test",
     "--editorial-package", "/tmp/nao-usar.json"],
])
def test_cli_rejects_incompatible_modes(monkeypatch, arguments):
    monkeypatch.setattr(sys, "argv", ["pipeline_rss.py", *arguments])
    with pytest.raises(SystemExit) as error:
        pipeline_rss.main()
    assert error.value.code == 2


def test_cli_saves_one_handoff_without_marking_seen(monkeypatch, tmp_path, capsys):
    import json
    from mkt_flow_p0.editorial_identity import validar_handoff_chatgpt
    item = {"titulo": "Android e agentes", "resumo": "Pesquisa",
            "link": URL, "fonte": "tecnoblog"}
    package = criar_handoff_chatgpt(ARTICLE, url_fonte=URL, fonte_nome="Fonte original")
    seen, processed = [], []

    def fake_process(*args, **kwargs):
        processed.append(kwargs)
        return {"acao": "pacote_editorial_criado", "escreveu": False,
                "editorial_handoff": package, "url": URL}

    _stub(monkeypatch, "rss_ingestor",
          FEEDS_PADRAO={"tecnoblog": "https://example.org/feed"},
          buscar_novidades=lambda *a, **k: {"novos": [item]},
          marcar_visto=lambda *a, **k: seen.append((a, k)))
    monkeypatch.setattr(pipeline_rss, "processar_item", fake_process)
    monkeypatch.setattr(sys, "argv", ["pipeline_rss.py", "--fonte", "tecnoblog",
                                     "--limit", "1", "--handoff-only",
                                     "--handoff-dir", str(tmp_path)])
    pipeline_rss.main()
    output = capsys.readouterr().out
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    assert validar_handoff_chatgpt(json.loads(files[0].read_text(encoding="utf-8")))["valid"]
    assert processed[0]["handoff_only"] is True
    assert '"pacote_editorial_criado": 1' in output
    assert seen == []

def test_handoff_only_does_not_download_external_image(monkeypatch):
    calls = _dependencies(monkeypatch)
    from mkt_flow_p0 import extractor, image_handler
    extractor.extrair_conteudo = lambda _: {
        "titulo": "Android e agentes", "texto": "Texto apurado " * 170,
        "qualidade_ok": True, "palavras": 340,
        "imagem": "https://example.org/protected-image.png"}
    def forbidden_image(*args, **kwargs):
        raise AssertionError("handoff-only should not fetch image bytes")
    image_handler.preparar_capa = forbidden_image
    monkeypatch.setenv("CONEXO_RSS_DRAFT", "1")
    result = pipeline_rss.processar_item(
        {"titulo": "Android e agentes", "resumo": "Pesquisa", "link": URL},
        handoff_only=True)
    assert result["acao"] == "pacote_editorial_criado"
    assert result["escreveu"] is False
    assert calls == []
