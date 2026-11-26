"""Regressões do orçamento e da resiliência do provedor. Sem rede real."""
import json
import sys
from types import SimpleNamespace

import pytest

import pipeline_rss
from mkt_flow_p0 import editorial_import
from mkt_flow_p0.editorial_development import ReviewProviderFailure
from mkt_flow_p0.provider_budget import (
    ProviderBudget, chamar_json, escopo_do_limite, estimar_tokens,
    modelo_disponivel, retry_after_exportado,
)


def _client(models=(), create=None):
    return SimpleNamespace(
        models=SimpleNamespace(list=lambda: SimpleNamespace(
            data=[SimpleNamespace(id=m) for m in models])),
        chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def test_estimar_tokens_sem_revelar_conteudo():
    n = estimar_tokens([{"role": "user", "content": "a" * 400}], 100)
    assert 200 <= n <= 220
    assert "a" * 400 not in str(n)


def test_budget_espera_antes_de_estourar_minuto():
    tempo = [0.0]
    esperas = []
    b = ProviderBudget(sleep=lambda s: (esperas.append(s), tempo.__setitem__(0, tempo[0] + s)),
                       clock=lambda: tempo[0], limite_tpm=100)
    b.registrar(tokens=80)
    assert b.esperar(20) == 60.0
    assert esperas == [60.0]
    assert b.status()["tokens_na_janela"] == 0


def test_retry_after_de_minuto_espera_e_de_dia_nao():
    tempo = [0.0]
    esperas = []
    b = ProviderBudget(sleep=lambda s: (esperas.append(s), tempo.__setitem__(0, tempo[0] + s)),
                       clock=lambda: tempo[0])
    b.registrar(tokens=10, escopo="tokens_per_minute", retry_after=12)
    b.registrar(tokens=10, escopo="tokens_per_day", retry_after=900)
    assert esperas == [12.0]
    assert b.espera_total == 12.0


def test_modelo_obsoleto_e_substituido_por_livre():
    cliente = _client(models=("qwen/qwen3.8-27b", "openai/gpt-oss-20b"))
    assert modelo_disponivel(cliente, "llama-3.3-70b-versatile") == "qwen/qwen3.8-27b"
    assert modelo_disponivel(cliente, "openai/gpt-oss-20b") == "openai/gpt-oss-20b"


class ErroJson(Exception):
    status_code = 400

    def __str__(self):
        return "Failed to validate JSON. Please adjust your prompt. json_validate_failed"


class ErroLimite(Exception):
    status_code = 429
    response = SimpleNamespace(headers={"retry-after": "12"})

    def __str__(self):
        return "429 tokens per minute exceeded SEGREDO_PROVEDOR"


def test_json_forcado_falha_e_reenvia_sem_response_format():
    chamadas = []

    def create(**kwargs):
        chamadas.append(kwargs)
        if len(chamadas) == 1:
            raise ErroJson()
        return SimpleNamespace(usage=SimpleNamespace(prompt_tokens=10, completion_tokens=20))

    resultado = chamar_json(_client(create=create), model="openai/gpt-oss-120b",
                            messages=[{"role": "user", "content": "Retorne JSON"}],
                            temperature=0, max_tokens=50, timeout=5,
                            budget=ProviderBudget(limite_tpm=8000))
    assert "response" in resultado
    assert len(chamadas) == 2
    assert chamadas[0]["response_format"] == {"type": "json_object"}
    assert "response_format" not in chamadas[1]


def test_limite_de_minuto_nao_vaza_corpo_do_provedor():
    def create(**kwargs):
        raise ErroLimite()

    resultado = chamar_json(_client(create=create), model="qwen/qwen3.8-27b",
                            messages=[{"role": "user", "content": "ok"}],
                            temperature=0, max_tokens=50, timeout=5,
                            budget=ProviderBudget(limite_tpm=8000))
    assert resultado["error_code"] == "PROVIDER_RATE_LIMIT"
    assert resultado["limit_scope"] == "tokens_per_minute"
    assert resultado["retry_after_seconds"] == 12
    assert "SEGREDO_PROVEDOR" not in json.dumps(resultado, ensure_ascii=False)
    assert escopo_do_limite(ErroLimite()) == "tokens_per_minute"
    assert retry_after_exportado(ErroLimite()) == 12


def test_falha_de_provedor_gera_pacote_pendente_sem_descartar_texto(tmp_path, monkeypatch):
    insumo = {
        "source_url": "https://example.org/fonte",
        "source_name": "Fonte",
        "research": {"sources": []},
        "article": {"titulo_seo": "T", "meta_description": "M", "slug": "s",
                    "texto_markdown": " ".join(["texto"] * 250)},
    }
    caminho = tmp_path / "insumo.json"
    caminho.write_text(json.dumps(insumo), encoding="utf-8")
    vistos = []

    def falso(path, handoff_dir, **kwargs):
        vistos.append(kwargs.get("offline"))
        if kwargs.get("offline") is False:
            raise ReviewProviderFailure("PROVIDER_RATE_LIMIT")
        return {"status": "PENDING", "article_complete_for_human_review": False}

    monkeypatch.setattr(editorial_import, "processar_artigo_importado", falso)
    monkeypatch.setattr(sys, "argv", ["pipeline_rss.py", "--import-article", str(caminho),
                                      "--handoff-only", "--handoff-dir", str(tmp_path / "saida")])
    assert pipeline_rss.main() == 0
    assert vistos == [False, True]
