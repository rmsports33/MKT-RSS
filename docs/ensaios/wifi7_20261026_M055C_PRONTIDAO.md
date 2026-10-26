# M05.5-C — Gate de prontidão para geração real em nuvem
Data: 2026-10-26. PR #20. Operação somente documental; não autoriza publicação.

## CI confirmada
- Commit bb0b08dcc73378cfb1cf32818864f62338d53602
- CI geral: run 40333021491, conclusion success.
- Validação editorial: run 40333022167, conclusion success.
- Ambos executados no GitHub Actions, sem Windows.

## Descoberta operacional — não executar chamada paga ainda
- `.env.example` documenta `GROQ_API_KEY`, `GROQ_MODEL` e taxas configuráveis; o arquivo de exemplo não demonstra autorização operacional nem existência de secret no executor.
- `mkt_flow_p0/rewriter.py` usa `GROQ_API_KEY` em `_get_client()` e limita `max_tokens` na chamada, mas `custo_usd_estimado` só é calculado **depois** da resposta. Não foi identificado neste caminho um gate explícito de orçamento antes de chamar a API.
- Preços no arquivo .env.example são valores configuráveis, não evidência de tarifa atual ou saldo do provedor.
- `pipeline_rss.py` permanece `verificacao_factual = "NAO_VERIFICADO"` e retorna `motivo = "gate_factual_pos_ia_nao_integrado"`, sem escrita.
- Não usar `workflow_dispatch` de tarefas de produção nem introduzir secrets em workflows novos para este ensaio.

## Próximo passo técnico de menor risco
1. Em branch isolada, implementar um runner experimental, explicitamente opt-in, que valide autorização, modelo, input real congelado, teto monetário calculado *antes* da API (ou fique em modo sem chamadas), e saída exclusivamente local ao job.
2. Nunca disponibilizar variáveis WP no job. Assegurar saída com `escreveu=False` e `NAO_VERIFICADO`.
3. Registrar snapshot íntegro da fonte com data de consulta e SHA-256, extração real, entrada/saída, tokens e custo efetivo; comparar corpo, título, metadados e JSON-LD.
4. Executar casos N1–N7, revisão independente e relatório de bloqueio/falha.
5. Nenhuma aprovação baseada somente em verde do CI ou `SEM_ALERTAS`.

## Resultado
CI remota PASSOU; execução com provedor real NÃO EXECUTADA (autorização de custo e pré-gate monetário não confirmados); factualidade NÃO CERTIFICADA; WordPress BLOQUEADO.
