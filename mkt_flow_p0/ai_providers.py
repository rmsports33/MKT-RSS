"""Provider-neutral, OpenAI-compatible AI transport.

The editorial modules intentionally keep their historical ``_get_client`` /
``chat.completions.create`` seam.  This module supplies that seam for Groq,
Gemini and OpenRouter without changing editorial contracts or gates.

Safety defaults:
* ``AI_FREE_ONLY=true``;
* ``AI_FALLBACK_ENABLED=false``;
* exact provider/model pairs are required (no suffix-only inference);
* secondary providers require an explicit allowlist entry.

This module never publishes, approves facts, retries a completed article, or
logs credentials/provider response bodies.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from types import SimpleNamespace
from typing import Any


TRUE = frozenset({"1", "true", "yes", "on"})

# These are provider-specific contracts, not a claim that quota is unlimited.
# A provider can still return 429; callers must preserve the source/article.
FREE_CATALOG = {
    ("groq", "llama-3.3-70b-versatile"),
    ("groq", "llama-3.1-8b-instant"),
    ("groq", "mixtral-8x7b-32768"),
    # Gemini/OpenRouter are deliberately not enabled by default.  They can be
    # enabled only with an exact, operator-reviewed allowlist entry.
}


class ProviderConfigurationError(RuntimeError):
    """A provider/model is not permitted by the current local policy."""


def _enabled(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    return default if raw is None else raw.strip().lower() in TRUE


def policy() -> dict:
    allowlist = {
        item.strip().lower()
        for item in os.getenv("AI_FREE_ONLY_ALLOWLIST", "").split(",")
        if item.strip()
    }
    return {
        "free_only": _enabled("AI_FREE_ONLY", True),
        "fallback_enabled": _enabled("AI_FALLBACK_ENABLED", False),
        "allowlist": sorted(allowlist),
    }


# Backward-compatible snapshots for callers that only need the defaults.  Code
# that changes environment variables at runtime must use policy() instead.
AI_FREE_ONLY = _enabled("AI_FREE_ONLY", True)
AI_FALLBACK_ENABLED = _enabled("AI_FALLBACK_ENABLED", False)


def _pair(provider: str, model: str) -> str:
    return f"{provider.strip().lower()}:{model.strip().lower()}"


def model_allowed(provider: str, model: str) -> bool:
    """Return whether a call is permitted, conservatively and exactly."""
    if not policy()["free_only"]:
        return True
    provider, model = provider.strip().lower(), model.strip()
    pair = _pair(provider, model)
    allowlist = set(policy()["allowlist"])
    if pair in allowlist:
        return True
    # Groq's default remains compatible with the old pipeline.  Gemini and
    # OpenRouter never become allowed merely because a name contains ':free'.
    return (provider, model) in FREE_CATALOG


def modelo_eh_gratuito(model: str, provider: str | None = None) -> bool:
    """Compatibility helper using the selected/default provider."""
    return model_allowed(provider or os.getenv("AI_PROVIDER", "groq"), model)


def _model(provider: str) -> str:
    env = {
        "groq": "GROQ_MODEL",
        "gemini": "GEMINI_MODEL",
        "openrouter": "OPENROUTER_MODEL",
    }[provider]
    defaults = {
        "groq": "llama-3.3-70b-versatile",
        "gemini": "gemini-2.0-flash",
        "openrouter": "",
    }
    return os.getenv(env, defaults[provider]).strip()


def _key_env(provider: str) -> str:
    return {
        "groq": "GROQ_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }[provider]


def _require(provider: str, model: str) -> str:
    if not model:
        raise ProviderConfigurationError(f"modelo {provider} ausente")
    if not model_allowed(provider, model):
        raise ProviderConfigurationError(
            f"modelo {model} bloqueado por AI_FREE_ONLY; "
            "use um par exato revisado em AI_FREE_ONLY_ALLOWLIST"
        )
    key = os.getenv(_key_env(provider), "").strip()
    if not key:
        raise ProviderConfigurationError(f"{_key_env(provider)} ausente")
    return key


def _response(content: str, *, finish_reason: str | None = None,
              usage: dict | None = None) -> Any:
    return SimpleNamespace(
        choices=[SimpleNamespace(
            finish_reason=finish_reason,
            message=SimpleNamespace(content=content),
        )],
        usage=SimpleNamespace(**(usage or {})),
    )


class _HTTPCompatibleClient:
    def __init__(self, provider: str, model: str, key: str):
        self.provider, self.model, self.key = provider, model, key
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, *, model, messages, temperature=0.5, max_tokens=2500,
               timeout=60, response_format=None, **_kwargs):
        if model != self.model:
            raise ProviderConfigurationError("modelo divergente do cliente")
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format is not None and self.provider == "openrouter":
            payload["response_format"] = response_format
        if self.provider == "gemini":
            text = "\n\n".join(
                f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages
            )
            payload = {
                "contents": [{"role": "user", "parts": [{"text": text}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "responseMimeType": "application/json",
                },
            }
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={self.key}"
            )
            headers = {"Content-Type": "application/json"}
        else:
            url = "https://openrouter.ai/api/v1/chat/completions"
            if self.provider == "groq":
                url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.key}",
            }
        req = urllib.request.Request(
            url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as result:
            body = json.loads(result.read().decode("utf-8"))
        if self.provider == "gemini":
            candidate = (body.get("candidates") or [{}])[0]
            parts = candidate.get("content", {}).get("parts", [])
            content = parts[0].get("text", "") if parts else ""
            finish = candidate.get("finishReason")
            finish = "length" if finish in {"MAX_TOKENS", "LENGTH"} else None
            return _response(content, finish_reason=finish)
        choice = (body.get("choices") or [{}])[0]
        return _response(
            choice.get("message", {}).get("content", ""),
            finish_reason=choice.get("finish_reason"),
            usage=body.get("usage") or {},
        )


def get_client(provider: str | None = None):
    """Return the historical ``client.chat.completions`` interface."""
    provider = (provider or os.getenv("AI_PROVIDER", "groq")).strip().lower()
    if provider not in {"groq", "gemini", "openrouter"}:
        raise ProviderConfigurationError("provedor desconhecido")
    model = _model(provider)
    key = _require(provider, model)
    if provider == "groq":
        try:
            from groq import Groq
        except ImportError:
            raise ProviderConfigurationError(
                "groq não instalado — rode: pip install groq"
            ) from None
        return Groq(api_key=key, max_retries=0), model
    return _HTTPCompatibleClient(provider, model, key), model


def provider_status() -> dict:
    p = (os.getenv("AI_PROVIDER", "groq") or "groq").strip().lower()
    model = _model(p) if p in {"groq", "gemini", "openrouter"} else ""
    return {
        **policy(),
        "provider": p,
        "model": model,
        "model_allowed": model_allowed(p, model) if model else False,
        "network_fallback": False,
    }


def politica_ativa() -> dict:
    """Portuguese compatibility alias for provider_status()."""
    return provider_status()


def gera_com_ia(*, messages: list | None = None, provider_name: str | None = None,
                model: str | None = None, system_prompt: str | None = None,
                prompt: str | None = None, **kwargs):
    """One-shot compatibility API returning parsed JSON and a safe error code.

    It deliberately performs one call only.  Fallback is never implicit.
    """
    if messages is None:
        messages = [
            {"role": "system", "content": system_prompt or ""},
            {"role": "user", "content": prompt or ""},
        ]
    client, selected = get_client(provider_name)
    response = client.chat.completions.create(
        model=model or selected, messages=messages, **kwargs
    )
    if getattr(response.choices[0], "finish_reason", None) == "length":
        return None, "RESPONSE_TRUNCATED"
    raw = response.choices[0].message.content or ""
    try:
        return json.loads(raw), None
    except (TypeError, ValueError, json.JSONDecodeError):
        return None, "RESPONSE_INVALID_JSON"
