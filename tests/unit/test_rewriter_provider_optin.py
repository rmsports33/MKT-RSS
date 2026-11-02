"""Testes offline da selecao opt-in do rewriter (Issue #16)."""
import sys
import types

from mkt_flow_p0 import rewriter as R


def test_default_groq_preservado(monkeypatch):
    monkeypatch.delenv("REWRITER_PROVIDER", raising=False)
    assert R._modelo() == "llama-3.3-70b-versatile"


def test_provedor_externo_requer_autorizacao(monkeypatch):
    monkeypatch.setenv("REWRITER_PROVIDER", "openai_compatible")
    monkeypatch.delenv("REWRITER_ALLOW_EXTERNAL_API", raising=False)
    _, erro = R._get_client()
    assert "desautorizada" in erro


def test_endpoint_inseguro_reprovado(monkeypatch):
    monkeypatch.setenv("REWRITER_PROVIDER", "openai_compatible")
    monkeypatch.setenv("REWRITER_ALLOW_EXTERNAL_API", "1")
    monkeypatch.setenv("OPENAI_COMPATIBLE_MODEL", "modelo-teste")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "chave-falsa")
    monkeypatch.setenv("REWRITER_ALLOWED_HOSTS", "api.exemplo.test")
    for url in ("http://api.exemplo.test/v1", "https://nao-autorizado.test/v1",
                "https://user:pass@api.exemplo.test/v1"):
        monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", url)
        client, erro = R._get_client()
        assert client is None and "nao permitido" in erro


def test_cliente_compativel_inicializa_sem_rede(monkeypatch):
    monkeypatch.setenv("REWRITER_PROVIDER", "openai_compatible")
    monkeypatch.setenv("REWRITER_ALLOW_EXTERNAL_API", "1")
    monkeypatch.setenv("OPENAI_COMPATIBLE_MODEL", "modelo-teste")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "chave-falsa")
    monkeypatch.setenv("REWRITER_ALLOWED_HOSTS", "api.exemplo.test")
    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", "https://api.exemplo.test/v1")
    class FakeClient:
        def __init__(self, **kwargs):
            self.params = kwargs
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=FakeClient))
    client, erro = R._get_client()
    assert erro == ""
    assert client.params["max_retries"] == 0
    assert client.params["base_url"] == "https://api.exemplo.test/v1"
    assert R._modelo() == "modelo-teste"


def test_openrouter_rejeita_modelo_pago(monkeypatch):
    monkeypatch.setenv("REWRITER_PROVIDER", "openai_compatible")
    monkeypatch.setenv("REWRITER_ALLOW_EXTERNAL_API", "1")
    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("REWRITER_ALLOWED_HOSTS", "openrouter.ai")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "chave-falsa")
    monkeypatch.setenv("OPENAI_COMPATIBLE_MODEL", "openai/gpt-4o")
    client, erro = R._get_client()
    assert client is None
    assert "nao gratuito bloqueado" in erro


def test_openrouter_free_mock_sem_chamada(monkeypatch):
    monkeypatch.setenv("REWRITER_PROVIDER", "openai_compatible")
    monkeypatch.setenv("REWRITER_ALLOW_EXTERNAL_API", "1")
    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("REWRITER_ALLOWED_HOSTS", "openrouter.ai")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "chave-falsa")
    monkeypatch.setenv("OPENAI_COMPATIBLE_MODEL", "openrouter/free")
    class FakeClient:
        def __init__(self, **kwargs):
            self.params = kwargs
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=FakeClient))
    client, erro = R._get_client()
    assert erro == ""
    assert client.params["base_url"] == "https://openrouter.ai/api/v1"
    assert R._modelo() == "openrouter/free"
