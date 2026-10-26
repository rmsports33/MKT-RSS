"""Custo fail-closed ANTES da API, apenas no piloto cloud isolado."""
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _ledger_piloto(monkeypatch, tmp_path):
    # Simular armazenamento persistente no escopo do teste, nao runner hospedado.
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setenv("CONEXO_CLOUD_LEDGER_PATH", str(tmp_path / "ledger.sqlite"))
    monkeypatch.setenv("CONEXO_CLOUD_DAILY_BUDGET_USD", "1.0")

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


def test_piloto_valido_respeita_limite_de_saida_sem_rede(monkeypatch):
    """Contraprova positiva: somente cliente injetado, sem rede e sem WP."""
    import json
    from types import SimpleNamespace
    from unittest.mock import Mock
    for key, val in BASE.items():
        monkeypatch.setenv(key, val)
    resposta = json.dumps({
        "titulo_seo": "Wi-Fi 7 e seus recursos",
        "meta_description": "Explicação dos recursos do Wi-Fi 7.",
        "slug": "wi-fi-7-recursos",
        "tags": ["wifi"],
        "texto_markdown": "Wi-Fi 7 tem recursos descritos pela fonte. " * 45,
    })
    completion = Mock(return_value=SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=resposta))],
        usage=SimpleNamespace(prompt_tokens=100, completion_tokens=200),
    ))
    client = SimpleNamespace(chat=SimpleNamespace(
        completions=SimpleNamespace(create=completion)))
    with patch.object(rewriter, "_get_client", return_value=(client, "")):
        resultado = rewriter.reescrever_materia("Wi-Fi 7", "texto fonte " * 120)
    assert "erro" not in resultado
    assert resultado["modelo"] == BASE["CONEXO_CLOUD_ALLOWED_MODEL"]
    assert resultado["uso_tokens"]["completion"] == 200
    assert resultado["custo_usd_estimado"] <= float(BASE["CONEXO_CLOUD_BUDGET_USD"])
    completion.assert_called_once()
    assert completion.call_args.kwargs["max_tokens"] == 250


def test_piloto_bloqueia_custo_nan(monkeypatch):
    r = _gerar(monkeypatch, {"CONEXO_CLOUD_BUDGET_USD": "nan"})
    assert "Piloto cloud bloqueado" in r["erro"]


def test_piloto_bloqueia_modelo_nao_permitido(monkeypatch):
    r = _gerar(monkeypatch, {"GROQ_MODEL": "modelo-desconhecido"})
    assert "Piloto cloud bloqueado" in r["erro"]


def test_ledger_acumulado_bloqueia_terceira_reserva(monkeypatch, tmp_path):
    from mkt_flow_p0.cloud_budget_ledger import reservar
    monkeypatch.setenv("CONEXO_CLOUD_LEDGER_PATH", str(tmp_path / "daily.sqlite"))
    monkeypatch.setenv("CONEXO_CLOUD_DAILY_BUDGET_USD", "0.002")
    assert reservar(0.001) == ""
    assert reservar(0.001) == ""
    assert "esgotado" in reservar(0.001)


def test_ledger_ausente_falha_fechada(monkeypatch):
    from mkt_flow_p0.cloud_budget_ledger import reservar
    monkeypatch.delenv("CONEXO_CLOUD_LEDGER_PATH")
    assert "Falha fechada" in reservar(0.001)


def test_ledger_nao_persistente_erro(monkeypatch, tmp_path):
    from mkt_flow_p0.cloud_budget_ledger import reservar
    monkeypatch.setenv("CONEXO_CLOUD_LEDGER_PATH", str(tmp_path / "missing" / "ledger.sqlite"))
    assert "nao disponivel" in reservar(0.001)


def test_github_actions_nao_usa_sqlite_efemero(monkeypatch, tmp_path):
    from mkt_flow_p0.cloud_budget_ledger import reservar
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("CONEXO_CLOUD_LEDGER_PATH", str(tmp_path / "ledger.sqlite"))
    monkeypatch.setenv("CONEXO_CLOUD_DAILY_BUDGET_USD", "1.0")
    assert "nao e compartilhado" in reservar(0.001)
    assert not (tmp_path / "ledger.sqlite").exists()
