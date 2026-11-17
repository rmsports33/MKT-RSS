# Verificação de conformidade com AGENTS.md — 17/11/2026

## Resultado: conforme

Cruzado AGENTS.md (111 linhas) com a branch operacional. Todas as diretrizes-chave
estão implementadas no mecanismo de elaboração de artigos e na infraestrutura:

| Diretriz | Status | Evidência |
|---|---|---|
| Gate humano por versão | ✅ | owner-release / validate_owner_release |
| Sem publicação automática | ✅ | publication_authorized; PENDING_HUMAN_REVIEW |
| Hash do DNA/prompt | ✅ | brief_sha256, prompt_sha256 no rewriter |
| Sem agendamento por padrão | ✅ | run_rss_queue.sh exige CONEXO_RSS_CRON_ACTIVE=1 |
| Um Gate, sem paralelo | ✅ | gate_unified.py único + CHECK_STAGES |
| Evidências rastreáveis | ✅ | evidence_ids / source_ids |
| Preço com data/mercado | ✅ | data_captura + validação de formato |
| IA não personifica humano | ✅ | HUMAN_ADAPTED exige editor + human_editorial_check |
| Rollback/readback | ✅ | padrão backup/readback |
| Independência de IA | ✅ | ai_providers.py, free-only, fallback=false |

## Pontos de atenção (riscos, não não-conformidade)
- PRs #71/#50 (repo privado): main.js versionado é artefato binário; correção real
  foi aplicada só no servidor. Não reabrir sem reconciliar.
- Cron de escrita da fila permanece DESATIVADO — correto conforme diretriz.
- Gate bloqueia corretamente as 4 claims Binance PENDING_HUMAN_REVIEW.

## Conclusão
Bloqueios ativos são proteções funcionando, não falhas. Nenhuma diretriz foi
violada. Nenhuma alteração feita nesta verificação (somente leitura).
