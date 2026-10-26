"""Custo fail-closed ANTES da API, apenas no piloto cloud isolado."""
from unittest.mock import patch

from mkt_flow_p0 import rewriter

BASE = {
    "CONEXO_CLOUD_PILOT": "1",
    "CONEXO_CLOUD_BUDGET_USD": "0.01",
    "CONEXO_CLOUD_MAX_INPUT_TOKENS": "10000",
    "CONEXO_CLOUD_MAX_OUTPUT_TOKENS": "250",
    "CONEXO_CLOUD_ALLOWED_MODEL": "llama-3.3-70b-versatile",
    "GROQ_MODEL": "llama-3.3-70b-versatile",
    "GROQ_COST_PER_1K_INPUT": "0.00015",
    "GROQ_COST_PER_1K_OUTPUT": "0.00075",
}


def _gerar(monkeypatch, overrides=None):
    for key in BASE:
        monkeypatch.delenv(key, raising=False)
    for key, val in {**BASE, **(overrides or {})}.items():
        if val is not None:
            monkeypatch.setenv(key, val)
    with patch.object(rewriter, "_get_client", side_effect=AssertionError("API nao pode ser acionada")):
        return rewriter.reescrever_materia("Titulo", "corpo " * 120)


def test_sem_orcamento_nao_toca_api(monkeypatch):
    r = _gerar(monkeypatch, {"CONEXO_CLOUD_BUDGET_USD": None})
    assert "Piloto cloud bloqueado" in r["erro"]


def test_sem_modelo_permitido_nao_toca_api(monkeypatch):
    r = _gerar(monkeypatch, {"CONEXO_CLOUD_ALLOWED_MODEL": "outro"})
    assert "Piloto cloud bloqueado" in r["erro"]


def test_custo_excede_orcamento_nao_toca_api(monkeypatch):
    r = _gerar(monkeypatch, {"CONEXO_CLOUD_BUDGET_USD": "0.00001"})
    assert "Piloto cloud bloqueado" in r["erro"]


def test_preco_invalido_nao_toca_api(monkeypatch):
    r = _gerar(monkeypatch, {"GROQ_COST_PER_1K_INPUT": "-0.1"})
    assert "Piloto cloud bloqueado" in r["erro"]


def test_limite_tokens_invalido_nao_toca_api(monkeypatch):
    r = _gerar(monkeypatch, {"CONEXO_CLOUD_MAX_OUTPUT_TOKENS": "5000"})
    assert "Piloto cloud bloqueado" in r["erro"]


def test_sem_credencial_em_configuracao_valida(monkeypatch):
    for key, val in BASE.items():
        monkeypatch.setenv(key, val)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with patch.object(rewriter, "_get_client", return_value=(None, "GROQ_API_KEY ausente")):
        r = rewriter.reescrever_materia("Titulo", "corpo " * 120)
    assert "GROQ_API_KEY ausente" in r["erro"]


def test_prompt_excede_teto_e_bloqueado(monkeypatch):
    r = _gerar(monkeypatch, {"CONEXO_CLOUD_MAX_INPUT_TOKENS": "1"})
    assert "Piloto cloud bloqueado" in r["erro"]
