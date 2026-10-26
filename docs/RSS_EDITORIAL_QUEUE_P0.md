# Fila inteligente de pautas RSS — P0

Implementação **opt-in** independente do pipeline legado e do WordPress.

## Uso

```bash
python rss_queue_collect.py --fonte 9to5google --limit 5
python rss_queue_collect.py --listar --limit 20
python -m pytest tests/test_fila_pautas.py -q
```

Sem `--fonte`, consulta as sete fontes já cadastradas. A coleta exige rede apenas para os feeds. O módulo `mkt_flow_p0.fila_pautas` não faz chamadas de rede e não invoca IA ou WordPress. Não existe agendamento novo. O pipeline `pipeline_rss.py` original permanece inalterado.

## Persistência e rastreabilidade

A tabela `rss_pautas` guarda URL normalizada, fonte, título, resumo, data original, estado, pontuação e timestamps. SQLite local é padrão; com `TURSO_DATABASE_URL` e `TURSO_AUTH_TOKEN`, reutiliza Turso por HTTP. Erro de Turso bloqueia a operação em vez de criar estado divergente local.

URLs idênticas ou com parâmetros de rastreamento removidos são deduplicadas; títulos similares (>=85%) são reconhecidos na janela dos últimos 200 registros. Estados: `DESCOBERTA`, `SELECIONADA`, `EM_PRODUCAO`, `EM_REVISAO`, `CONCLUIDA`, `REJEITADA` e `BLOQUEADA`. Mudar estado é uma operação explícita de software; nenhuma transição aprova, certifica ou publica matéria.

A pontuação inicial é heurística, transparente e determinística; não contém sinais externos de pesquisa, veracidade ou monetização. Não automatiza escolha editorial. Resultados de coleta não autorizam publicação.

## Limites da entrega

- A execução do coletor legado não é alterada; a migração gradual exigirá uma segunda tarefa e aceite.
- Sem retries transacionais avançados nem agrupamento semântico multilíngue nesta fase.
- Concorrência entre coletores remotos demanda validação de idempotência específica antes de agendamentos.
- Nenhum agendador, API paga, mudança nos gates de WordPress, deploy ou publicação.
