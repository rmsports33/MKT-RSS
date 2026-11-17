# Fase 3 — Shopee → Turso homolog — 17/11/2026

## M18 CONCLUÍDO

 homolog | resultado |
|---|---|
| `--check` | `{"ok": true, "local_records": 1, "remote_write": false, "ids": ["57613c2df5f3"]}` |
| `--apply` | `{"ok": true, "total_local": 1, "new_remote_rows": 1, "exact_readback": 1}` |
| `--verify` | `{"ok": true, "total_local": 1, "new_remote_rows": 0, "exact_readback": 1}` |

- Destino: `libsql://mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io`
- Token: environment `rss-homolog` (GitHub Secrets), nunca no repo/chat
- Integração: scripts do `master` trazidos para a operacional via cherry-pick
  (`7e25ffa`, `44b4f74`, `918c765`); 7 testes passando
- `new_remote_rows: 0` no verify prova idempotência (sem duplicação)
- Nenhum token RSS de 7 dias reutilizado; nenhuma escrita no banco principal

## M17 — PR #122 (multi-IA) — próximo
Draft, base `feat/hostinger-runtime-independente-20261113`, head `feat/ai-provider-independent`.
Pendente: testes Linux e homologação Gemini/OpenRouter; manter Groq padrão, fallback desligado.
