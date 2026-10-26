"""Fluxo real de redação/formatacao/gates; fronteiras externas simuladas."""
import json
import socket
from types import SimpleNamespace

import pytest
import pipeline_rss
from mkt_flow_p0 import extractor, format as formatter, rewriter, seo


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Rede proibida na validação editorial")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.delenv("GATE_PUBLICACAO_ENABLED", raising=False)
    # Mesmo com credenciais aparentes, nenhum caminho de escrita deve existir.
    for key in ("WP_URL", "WP_USER", "WP_APP_PASSWORD"):
        monkeypatch.setenv(key, "fixture-sem-credencial-real")


@pytest.mark.parametrize("extra,expected", [
    ("", "SEM_ALERTAS"),
    (" A bateria tem 99999 mAh.", "BLOQUEADO"),
    (" Testamos o notebook em nosso laboratório.", "BLOQUEADO"),
])
def test_source_to_final_html_keeps_wp_blocked(monkeypatch, extra, expected):
    sentence = "O notebook recebeu uma atualização documentada para ampliar a compatibilidade dos aplicativos."
    source = " ".join([sentence] * 25)
    generated = source + extra
    observed = {}
    def completion(**kwargs):
        observed["prompt"] = kwargs["messages"]
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({
                "titulo_seo": "Notebook recebe atualização",
                "texto_markdown": generated, "tags": ["notebook"],
            })))],
            usage=SimpleNamespace(prompt_tokens=0, completion_tokens=0),
        )
    client = SimpleNamespace(chat=SimpleNamespace(
        completions=SimpleNamespace(create=completion)))
    monkeypatch.setattr(rewriter, "_get_client", lambda: (client, ""))
    monkeypatch.setattr(extractor, "extrair_conteudo", lambda url: {
        "titulo": "Notebook recebe atualização", "texto": source,
        "palavras": len(source.split()), "qualidade_ok": True,
    })
    monkeypatch.setattr(seo, "enriquecer_com_keywords", lambda *a, **kw: [])
    actual_format = formatter.markdown_para_html
    def record_html(markdown):
        observed["html"] = actual_format(markdown)
        return observed["html"]
    monkeypatch.setattr(formatter, "markdown_para_html", record_html)
    result = pipeline_rss.processar_item({
        "titulo": "Notebook recebe atualização", "resumo": sentence,
        "fonte": "Fonte sintética", "link": "https://fonte.example/notebook",
    })
    assert observed["html"].startswith("<p>")
    assert "Fonte original" in observed["html"]
    assert "https://fonte.example/notebook" in observed["html"]
    assert result["auditoria_pos_ia"]["veredito"] == expected
    assert result["verificacao_factual"] == "NAO_VERIFICADO"
    assert result["acao"] == "bloqueado" and result["escreveu"] is False
    assert result["auditoria_evidencias"]["veredito"] == "BLOQUEADO"
    assert observed["prompt"]  # rewriter real recebeu a entrada e parseou JSON.


def test_source_failure_never_generates_content(monkeypatch):
    monkeypatch.setattr(extractor, "extrair_conteudo",
                        lambda url: {"erro": "captura indisponível"})
    def forbidden(*a, **kw):
        raise AssertionError("LLM não deve receber captura que falhou")
    monkeypatch.setattr(rewriter, "_get_client", forbidden)
    result = pipeline_rss.processar_item({
        "titulo": "Notebook recebe atualização", "resumo": "Aplicativos do notebook",
        "link": "https://fonte.example/notebook",
    })
    assert result["acao"] == "falha"
