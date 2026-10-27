# Fila inteligente de pautas RSS — P0

Implementação **opt-in** independente do pipeline legado e do WordPress.

## Uso

```bash
python rss_queue_collect.py --fonte 9to5google --limit 5
python pipeline_rss.py --queue-only --fonte 9to5google --limit 5
python rss_queue_collect.py --listar --limit 20
python -m pytest tests/test_fila_pautas.py -q
```

Sem `--fonte`, consulta as sete fontes já cadastradas. A coleta exige rede apenas para os feeds. O módulo `mkt_flow_p0.fila_pautas` não faz chamadas de rede e não invoca IA ou WordPress. Não existe agendamento novo. O pipeline `pipeline_rss.py` inclui somente a opção explícita `--queue-only`, que despacha para a coleta de pautas e retorna sem gerar texto ou contactar WordPress; sem essa opção, o fluxo legado segue inalterado. `--queue-only --dry-run` é rejeitado.

## Persistência e rastreabilidade

A tabela `rss_pautas` guarda URL normalizada, fonte, título, resumo, data original, estado, pontuação e timestamps. SQLite local é padrão; com `TURSO_DATABASE_URL` e `TURSO_AUTH_TOKEN`, reutiliza Turso por HTTP. Erro de Turso bloqueia a operação em vez de criar estado divergente local.

URLs idênticas ou com parâmetros de rastreamento removidos são deduplicadas; títulos similares (>=85%) são reconhecidos na janela dos últimos 200 registros. Estados: `DESCOBERTA`, `SELECIONADA`, `EM_PRODUCAO`, `EM_REVISAO`, `CONCLUIDA`, `REJEITADA` e `BLOQUEADA`. Mudar estado é uma operação explícita de software; nenhuma transição aprova, certifica ou publica matéria.

A pontuação inicial é heurística, transparente e determinística; não contém sinais externos de pesquisa, veracidade ou monetização. Não automatiza escolha editorial. Resultados de coleta não autorizam publicação.

## Limites da entrega

- O comportamento do coletor legado sem `--queue-only` não é alterado; ativação operacional/agendamento exige etapa separada.
- Sem retries transacionais avançados nem agrupamento semântico multilíngue nesta fase.
- Concorrência entre coletores remotos demanda validação de idempotência específica antes de agendamentos.
- Nenhum agendador, API paga, mudança nos gates de WordPress, deploy ou publicação.

## Validação remota e decisão cloud-first (27/10/2026)

Prova real **concluída** no run [40503549660](https://github.com/rmsports33/MKT-RSS/actions/runs/40503549660), job `rss_queue_live_probe`: feed 9to5Google, primeira passagem 3 novas/0 duplicadas, segunda 0 novas/3 duplicadas, três IDs preservados **no mesmo runner e banco SQLite temporário**. O job de rede foi removido do CI depois de coletar a evidência; não deve ser executado em todo PR.

**Avaliação de persistência:** a implementação da fila usa `cloud_db.turso_enabled()` e `cloud_db.turso_execute()` já existentes; exige `TURSO_DATABASE_URL` e `TURSO_AUTH_TOKEN`. Se houver configuração remota e a operação falhar, a fila falha fechada, não cria estado divergente local. Sem esses parâmetros, usa SQLite. Isso demonstra compatibilidade de código com Turso, **não** comprova banco remoto existente, credenciais válidas, continuidade entre runs ou segurança sob coletores concorrentes. Não configurar/usar segredos de produção por inferência.

**Risco residual:** operações `SELECT` seguido de `INSERT` são separadas: o índice de URL previne duplicata por ID, mas a comparação aproximada de títulos não é transacional entre trabalhadores concorrentes. Não habilitar coleta paralela/agendada até validar serialização ou mecanismo atômico adequado. SQLite no runner efêmero não persiste entre runs; Turso é candidato para persistência real, condicionado à verificação supervisionada de disponibilidade e custos.

**Próxima validação específica:** com base remota de testes explicitamente autorizada, executar duas execuções independentes usando o mesmo Turso, sem WordPress e confirmar IDs/duplicatas. Se não existir ambiente apropriado, manter a fila opt-in e bloquear agendamentos. Sem novos provedores, servidores, merge, deploy ou publicação.
