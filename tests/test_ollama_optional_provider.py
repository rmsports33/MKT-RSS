"""Offline Ollama integration tests: no downloads, sockets or WordPress writes."""
import json
from unittest.mock import Mock

import pytest
from mkt_flow_p0 import ai_providers


def test_default_provider_remains_groq(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_FALLBACK_ENABLED", raising=False)
    assert ai_providers.provider_status()["provider"] == "groq"
    assert ai_providers.provider_status()["fallback_enabled"] is False


def test_ollama_is_local_free_only_model(monkeypatch):
    monkeypatch.setenv("AI_FREE_ONLY", "true")
    monkeypatch.delenv("AI_FREE_ONLY_ALLOWLIST", raising=False)
    assert ai_providers.model_allowed("ollama", "qwen3:4b")
    assert ai_providers.model_allowed("ollama", "qwen2.5:7b")
    assert not ai_providers.model_allowed("ollama", "model-that-wasnt-reviewed")


def test_ollama_calls_only_loopback_with_no_authorization_header(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:4b")
    monkeypatch.setenv("AI_FREE_ONLY", "true")
    monkeypatch.delenv("AI_FREE_ONLY_ALLOWLIST", raising=False)
    seen = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return json.dumps({
                "choices": [{"message": {"content": '{"ok":true}'},
                             "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 2}
            }).encode()

    def fake_open(request, timeout):
        seen["url"] = request.full_url
        seen["headers"] = dict(request.header_items())
        seen["body"] = json.loads(request.data)
        return Response()

    monkeypatch.setattr(ai_providers.urllib.request, "urlopen", fake_open)
    client, model = ai_providers.get_client()
    result = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": "teste"}],
        response_format={"type": "json_object"},
    )
    assert seen["url"] == "http://127.0.0.1:11434/v1/chat/completions"
    assert "Authorization" not in seen["headers"]
    assert seen["body"]["response_format"] == {"type": "json_object"}
    assert result.choices[0].message.content == '{"ok":true}'


def test_unknown_ollama_model_is_blocked_before_transport(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "unknown:70b")
    monkeypatch.setenv("AI_FREE_ONLY", "true")
    monkeypatch.delenv("AI_FREE_ONLY_ALLOWLIST", raising=False)
    network = Mock()
    monkeypatch.setattr(ai_providers.urllib.request, "urlopen", network)
    with pytest.raises(ai_providers.ProviderConfigurationError):
        ai_providers.get_client()
    network.assert_not_called()
