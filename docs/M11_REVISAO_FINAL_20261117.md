# M11 — Revisão final do binance_stage — 17/11/2026

## Resultado da homologação no servidor

```
ERRORS: []
BLOCKERS: 4× alegação não conferida + revisão separada + aceite humano
PRONTO PARA STAGE: False
```

Estrutura do pacote `editorial-workflow/2` **100% válida** (20 erros → 0). Restam
apenas os 6 blockers que exigem verificação humana autêntica.

## O que foi entregue (real e versionado)

| Item | Commit / evidência |
|------|--------------------|
| Core editorial instalado no servidor | 5 SHA-256 verificados contra lock |
| `binance_gate_stage.py` (stage via Gate, fail-closed, lê token) | `63d9599` |
| `build_binance_package.py` (mapeia dados reais do handoff) | `b32fa4c` |
| 13 testes de contrato passando | local + servidor |
| `job_id` `binance-stage-20261117-001` preservado | NÃO publicado |

## Campos mapeados de DADOS REAIS do handoff

- `title`, `article_id`, `slug`, `content` (wordpress-body.html)
- `author`, `durability`, `audience`, `question`, `contribution`, `brazil_context`, `disclosure` (editorial_brief)
- `directives` (3 arquivos do core com hashes reais)
- `sources` (4 URLs com publisher derivado do domínio + checked_at do mtime real)
- `claims` (4 claims reais, status UNKNOWN — verificação não fabricada)
- `keyword_research`, `editorial_decision`, `process_steps` (do pipeline-report real)
- `images` (Unsplash: origem, licença, crédito, alt, sha256 reais)
- `substantive_review` (schema editorial-substance/1, excerpts reais localizados no corpo)
- `related_articles` (3 links internos reais presentes no HTML, com scope internal)

## Blockers restantes — LEGÍTIMOS, não devem ser burlados

1. `alegação não conferida: extra_1_1` a `extra_4_1` — as 4 claims estão
   `PENDING_HUMAN_REVIEW` no handoff; verificação factual não foi feita.
2. `revisão separada da versão pendente` — não existe auditoria independente em `reviews[]`.
3. `aceite humano da versão pendente` — não há aceite do revisor.

Marcar qualquer um como PASS sem evidência real seria **falsificar verificação
humana** — proibido pelas regras do projeto. O Gate está funcionando corretamente.

## Conclusão

O `binance_stage` **não deve rodar** até que o fluxo editorial (P2/P3) produza:
- conferência factual das 4 claims com evidência real;
- revisão separada (`reviews[]` com 10 checks e contexto independente);
- aceite humano vinculado à versão `a80b3e39...`.

A infraestrutura (core, stage, builder, token, pacote válido) está pronta. Falta a
revisão humana autêntica — que é justamente o que o Gate protege. Nenhuma
publicação, nenhum `job_id` queimado, nenhuma credencial exposta.

## Próxima frente
Fase 3 — Shopee → Turso homolog (`--check → --apply → --verify`) e PR #122 (multi-IA).
