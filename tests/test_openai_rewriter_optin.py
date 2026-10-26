"""OpenAI adapter must fail closed without separate API billing authorization."""
import types

from mkt_flow_p0 import rewriter


def test_api_disabled_no_client(monkeypatch):
    monkeypatch.delenv("CONEXO_OPENAI_API_ENABLED", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "not-used")
    client, error = rewriter._get_client()
    assert client is None and "desativada" in error


def test_missing_key_no_client(monkeypatch):
    monkeypatch.setattr(rewriter, "_ensure_env", lambda: None)
    monkeypatch.setenv("CONEXO_OPENAI_API_ENABLED", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client, error = rewriter._get_client()
    assert client is None and "OPENAI_API_KEY" in error


def test_missing_model_no_client(monkeypatch):
    monkeypatch.setattr(rewriter, "_ensure_env", lambda: None)
    monkeypatch.setenv("CONEXO_OPENAI_API_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "example-not-real")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    client, error = rewriter._get_client()
    assert client is None and "OPENAI_MODEL" in error


def test_no_api_call_on_disabled_path(monkeypatch):
    monkeypatch.delenv("CONEXO_OPENAI_API_ENABLED", raising=False)
    result = rewriter.reescrever_materia("Título", " ".join(["texto"] * 110))
    assert "erro" in result and "desativada" in result["erro"]


def test_openai_response_contract_injected(monkeypatch):
    seen = {}
    def create(**kwargs):
        seen.update(kwargs)
        import json
        return types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=json.dumps({
                "titulo_seo": "Título teste",
                "texto_markdown": " ".join(["Frase de teste."] * 210),
                "tags": ["teste"], "slug": "titulo-teste",
            })))],
            usage=types.SimpleNamespace(prompt_tokens=10, completion_tokens=20),
        )
    client = types.SimpleNamespace(chat=types.SimpleNamespace(
        completions=types.SimpleNamespace(create=create)))
    monkeypatch.setattr(rewriter, "_get_client", lambda: (client, ""))
    monkeypatch.setenv("OPENAI_MODEL", "example-model-injected")
    result = rewriter.reescrever_materia("Título", " ".join(["texto"] * 110))
    assert "erro" not in result
    assert seen["model"] == "example-model-injected"
    assert result["uso_tokens"]["total"] == 30
    assert result["modelo"] == "example-model-injected"
