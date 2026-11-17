# Fase 3 — chaves de IA configuradas — 17/11/2026

## M17 — multi-IA HOMOLOGADO

- `ai_providers.py` integrado na operacional (commit `f835b4f`), 8 testes.
- Chaves em `~/.config/conexo-os/ai-keys.env` (modo 0600, nunca no repo/chat):
  `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_MODEL`, `OPENROUTER_MODEL`.
- Allowlist explicita do operador adicionada:
  `AI_FREE_ONLY_ALLOWLIST=gemini:gemini-2.0-flash,openrouter:google/gemini-2.0-flash:free`

### Validacao (servidor)
```
groq/gemini/openrouter key= True
allowlist = ['gemini:gemini-2.0-flash', 'openrouter:google/gemini-2.0-flash:free']
model_allowed(gemini) = True
model_allowed(openrouter) = True
free_only=True, fallback_enabled=False, network_fallback=False
```

Groq permanece o provedor padrao. Gemini/OpenRouter podem ser usados sem
fallback automatico. Guia de configuracao: `ops/hostinger/CONFIG_AI_KEYS_20261117.md`.

## Fase 3 COMPLETA
- M18 Shopee → homolog: check/apply/verify OK, idempotente, readback exato.
- M17 multi-IA: homologado com 3 provedores, free-only, sem fallback.
