"""Offline provider-adapter regressions; no credentials and no network."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from mkt_flow_p0 import ai_providers
from mkt_flow_p0 import rewriter


class _HTTPResponse:
    def __init__(self, body):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


def test_safe_defaults_and_exact_free_catalog(monkeypatch):
    monkeypatch.delenv("AI_FREE_ONLY", raising=False)
    monkeypatch.delenv("AI_FALLBACK_ENABLED", raising=False)
    monkeypatch.delenv("AI_FREE_ONLY_ALLOWLIST", raising=False)
    assert ai_providers.policy()["free_only"] is True
    assert ai_providers.policy()["fallback_enabled"] is False
    assert ai_providers.modelo_eh_gratuito("llama-3.3-70b-versatile", "groq")
    assert not ai_providers.modelo_eh_gratuito("gpt-4o-mini", "groq")
    # A suffix is not a billing proof by itself.
    assert not ai_providers.modelo_eh_gratuito("some-model:free", "openrouter")


def test_secondary_provider_requires_exact_allowlist(monkeypatch):
    monkeypatch.setenv("AI_FREE_ONLY", "true")
    monkeypatch.delenv("AI_FREE_ONLY_ALLOWLIST", raising=False)
    assert not ai_providers.model_allowed("gemini", "gemini-2.0-flash")
    monkeypatch.setenv(
        "AI_FREE_ONLY_ALLOWLIST", "gemini:gemini-2.0-flash,openrouter:vendor/model:free"
    )
    assert ai_providers.model_allowed("gemini", "gemini-2.0-flash")
    assert ai_providers.model_allowed("openrouter", "vendor/model:free")
    assert not ai_providers.model_allowed("openrouter", "vendor/other:free")


def test_paid_model_is_rejected_before_any_request(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "vendor/paid-model")
    network = Mock()
    monkeypatch.setattr(ai_providers.urllib.request, "urlopen", network)
    with pytest.raises(ai_providers.ProviderConfigurationError):
        ai_providers.get_client()
    network.assert_not_called()


def test_gemini_http_response_is_normalized(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.0-flash")
    monkeypatch.setenv("AI_FREE_ONLY_ALLOWLIST", "gemini:gemini-2.0-flash")

    body = json.dumps({
        "candidates": [{
            "content": {"parts": [{"text": '{"ok": true}'}]},
            "finishReason": "STOP",
        }]
    }).encode()
    response = _HTTPResponse(body)
    monkeypatch.setattr(ai_providers.urllib.request, "urlopen", lambda *a, **k: response)
    client, model = ai_providers.get_client()
    result = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": "x"}]
    )
    assert result.choices[0].message.content == '{"ok": true}'


def test_openrouter_http_response_is_normalized(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "vendor/model:free")
    monkeypatch.setenv("AI_FREE_ONLY_ALLOWLIST", "openrouter:vendor/model:free")

    body = json.dumps({
        "choices": [{
            "message": {"content": '{"ok": true}'},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 2, "completion_tokens": 3},
    }).encode()
    response = _HTTPResponse(body)
    monkeypatch.setattr(ai_providers.urllib.request, "urlopen", lambda *a, **k: response)
    client, model = ai_providers.get_client()
    result = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": "x"}]
    )
    assert result.choices[0].message.content == '{"ok": true}'
    assert result.usage.prompt_tokens == 2


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("401 invalid_api_key", "GROQ_API_KEY inválida"),
        ("429 tokens per day", "PROVIDER_RATE_LIMIT"),
        ("timeout while reading", "Falha Groq"),
    ],
)
def test_legacy_rewriter_error_contract_remains_fail_closed(
    monkeypatch, message, expected
):
    class Completions:
        def create(self, **kwargs):
            raise RuntimeError(message)

    client = SimpleNamespace(chat=SimpleNamespace(completions=Completions()))
    monkeypatch.setattr(rewriter, "_get_client", lambda: (client, ""))
    result = rewriter.reescrever_materia(
        "Título", "palavra " * 120, editorial_brief={
            "genre": "noticia",
            "reader": "Leitores técnicos que precisam de contexto verificável.",
            "need": "Entender limites do material fornecido.",
            "angle": "Separar documento de hipótese.",
            "contribution": "Explicar consequências sem inventar fatos.",
            "limits": "Não inventar testes, preços ou experiência.",
        }
    )
    assert "erro" in result
    if expected == "PROVIDER_RATE_LIMIT":
        assert result["error_code"] == expected
    else:
        assert expected in result["erro"]


def test_gemini_preserves_system_and_assistant_roles_and_hides_api_key(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "secret-test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.0-flash")
    monkeypatch.setenv("AI_FREE_ONLY_ALLOWLIST", "gemini:gemini-2.0-flash")

    captured = {}
    body = json.dumps({
        "candidates": [{
            "content": {"parts": [{"text": '{"ok": true}'}]},
            "finishReason": "STOP",
        }]
    }).encode()

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _HTTPResponse(body)

    monkeypatch.setattr(ai_providers.urllib.request, "urlopen", fake_urlopen)
    client, model = ai_providers.get_client()
    client.chat.completions.create(model=model, messages=[
        {"role": "system", "content": "Preserve editorial rules."},
        {"role": "user", "content": "Source facts."},
        {"role": "assistant", "content": "Prior analysis."},
        {"role": "user", "content": "Write the article."},
    ])

    assert "secret-test-key" not in captured["url"]
    assert "key=" not in captured["url"]
    assert captured["headers"].get("X-goog-api-key") == "secret-test-key"
    assert captured["payload"]["systemInstruction"]["parts"][0]["text"] == "Preserve editorial rules."
    assert captured["payload"]["contents"] == [
        {"role": "user", "parts": [{"text": "Source facts."}]},
        {"role": "model", "parts": [{"text": "Prior analysis."}]},
        {"role": "user", "parts": [{"text": "Write the article."}]},
    ]



def test_gemini_joins_content_parts_with_real_newlines(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "secret-test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.0-flash")
    monkeypatch.setenv("AI_FREE_ONLY_ALLOWLIST", "gemini:gemini-2.0-flash")

    captured = {}
    body = json.dumps({
        "candidates": [{
            "content": {"parts": [{"text": '{"ok": true}'}]},
            "finishReason": "STOP",
        }]
    }).encode()

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return _HTTPResponse(body)

    monkeypatch.setattr(ai_providers.urllib.request, "urlopen", fake_urlopen)
    client, model = ai_providers.get_client()
    client.chat.completions.create(model=model, messages=[
        {"role": "system", "content": [{"text": "Rule one"}, {"text": "Rule two"}]},
        {"role": "system", "content": "Additional rule"},
        {"role": "user", "content": [{"text": "Source part"}, {"text": "Verified fact"}]},
    ])

    assert captured["payload"]["systemInstruction"]["parts"][0]["text"] == (
        "Rule one\\nRule two\\n\\nAdditional rule"
    )
    assert captured["payload"]["contents"] == [
        {"role": "user", "parts": [{"text": "Source part\\nVerified fact"}]},
    ]
