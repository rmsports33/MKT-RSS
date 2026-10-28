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

## Decisão específica de persistência e concorrência (27/10/2026)

**Teste acrescentado:** `test_turso_simulado_preserva_entre_chamadas_independentes` exercita o adaptador `turso_execute` contra um backend SQLite isolado, preservando registros entre invocações da API. É uma prova offline de compatibilidade de interface — **não** é validação do serviço Turso real, de persistência entre jobs ou de latência/conectividade.

**Verificação de ambiente:** o código requer `TURSO_DATABASE_URL` e `TURSO_AUTH_TOKEN`, mas uma base Turso **isolada e autorizada** não foi identificada nesta sessão. Não reutilizar banco de produção, não exibir segredos, não configurar serviços ou gastos silenciosamente. Resultado remoto: `BLOQUEADO_POR_AMBIENTE_NAO_CONFIRMADO`.

**Concorrência avaliada:** o identificador SHA-256 da URL canônica tem restrição `PRIMARY KEY`, então `INSERT OR IGNORE` evita duas linhas da mesma URL, embora o sinal `novo` dependa de contagem de linhas. Para URLs diferentes com títulos similares, a leitura dos 200 títulos e a escrita ocorrem fora de uma transação serializável: dois workers podem passar juntos pelo filtro aproximado e inserir duas pautas. O mesmo vale para `mudar_estado` em backend remoto: a atualização condicional protege contra alteração do estado que mudou, mas necessita observar a contagem de linhas afetadas.

**Critério para liberar execução contínua:** demonstrar uma base de testes distinta, rodar duas tarefas independentes apontando ao mesmo banco e realizar teste de dois coletores concorrentes; se a deduplicação aproximada falhar, implementar transação/serialização na camada de persistência, com testes. Até isso ocorrer, **não agendar, não operar em paralelo e não integrar ao master automaticamente**.

## Proteção de gravação concorrente (27/10/2026)

O registro de pauta agora reserva um **lease de escrita único** na tabela `rss_queue_mutex`, compartilhada entre coletores apontando para o mesmo SQLite ou Turso. Um segundo coletor concorrente falha de modo controlado, sem avaliar similaridade sobre snapshot desatualizado nem criar outra pauta. O lease é liberado por `finally` mesmo diante de falha. Após interrupção abrupta, expira em **300 segundos**; não existe renovação automática.

Essa estratégia garante **exclusão durante a janela do lease**, não processamento paralelo: sob contenção o segundo coletor deve tentar novamente de forma supervisionada. Se um processamento dentro da seção crítica ultrapassar 300 segundos, a exclusão poderá expirar; antes de habilitar vários workers ou operação permanente, validar esse limite e testar o protocolo no serviço Turso real. Como a fila usa chamadas HTTP separadas, a sequência não é uma transação única; a reserva de exclusividade é uma coordenação lógica no mesmo banco.

Testes offline cobrem disputa entre threads de dois coletores, deduplicação de título similar após liberação, recuperação do lease após erro e adaptador Turso simulado. **Não** constituem teste de duas máquinas/runners independentes usando banco Turso real. Sem infraestrutura de produção ou agendamento nesta entrega.

## Checkpoint final de prontidão — 28/10/2026

**Escopo entregue:** fila de pautas opt-in, deduplicação independente de WordPress, ranking heurístico, estados editoriais, armazenamento SQLite/Turso e comando `pipeline_rss.py --queue-only`. A execução sem essa flag permanece no fluxo legado; o modo opt-in não autoriza WordPress.

**CI do HEAD técnico final `8933c8f6f9baa74a7dc7ae63ef4446ffd60d09c2`:** [execução 40687955253](https://github.com/rmsports33/MKT-RSS/actions/runs/40687955253) SUCCESS, 566 testes núcleo + 52 redator = **618 testes aprovados**; validação editorial [40687955888](https://github.com/rmsports33/MKT-RSS/actions/runs/40687955888) SUCCESS. Uma alteração documental posterior requer checagem própria do CI; esses números não devem ser atribuídos automaticamente a commits posteriores.

**Evidências reais isoladas:**
- [Coleta RSS 40503549660](https://github.com/rmsports33/MKT-RSS/actions/runs/40503549660): três novas na primeira passagem, três duplicatas na segunda, SQLite temporário no mesmo runner.
- [Persistência Turso 40687421115](https://github.com/rmsports33/MKT-RSS/actions/runs/40687421115): runner seed `new=true`, runner verify `duplicate=true, persisted=true`, mesmo ID em banco **mkt-rss-homolog**.
- [Concorrência Turso 40687825993](https://github.com/rmsports33/MKT-RSS/actions/runs/40687825993): dois runners sincronizados; um registrou `novo=true`, outro `bloqueado_por_concorrencia=true`; conferência retornou **um único ID**. Prova circunscrita ao cenário e carga testados.

**Condições obrigatórias antes de operar:** não iniciar agendador, nem paralelismo contínuo; o lease de escrita expira em 300 segundos, sem renovação, e não há certificação sob cargas longas. Não converter `CONCLUIDA` em autorização de publicação. Não usar o banco `mkt-rss` de produção para homologação, nem revelar segredos. Scripts `scripts/rss_queue_turso_homolog_probe.py` e `scripts/rss_queue_turso_concurrency_probe.py` ficam preservados como instrumentos manuais de laboratório; os jobs temporários foram retirados de `.github/workflows/ci.yml`.

**Decisão:** PR tecnicamente validado nos cenários descritos e candidato a integração **somente de código** após revisão/aceite separados. Merge, deploy, ativação da coleta, paralelismo e publicação são decisões distintas e não estão autorizadas por este documento.


## Checkpoint operacional P0 — 28/10/2026 (pós-merge)

**Integração:** PR #28 integrado por squash ao `master`, commit `3890eeaa0d3a12b24bfc5b8d934eba5ce48304fe`. CI de `push` pós-merge `CI (pytest) #255` aprovado, conforme captura do GitHub Actions fornecida pelo operador. O workflow manual de homologação foi configurado no `master` em `.github/workflows/rss-homolog-manual.yml`; ambiente `rss-homolog` com branch `master` autorizada e secrets protegidos.

**Coleta real controlada (fonte 9to5google; limite 3; `--queue-only`; banco isolado `mkt-rss-homolog`):**

| Etapa | GitHub Actions | Resultado do log |
| --- | --- | --- |
| Primeira execução | [40701814910](https://github.com/rmsports33/MKT-RSS/actions/runs/40701814910) | `{"novas":3,"duplicadas":0,"falhas":[]}` |
| Segunda execução independente | [40702439180](https://github.com/rmsports33/MKT-RSS/actions/runs/40702439180) | `{"novas":0,"duplicadas":3,"falhas":[]}` |

**Conclusão P0:** coleta de feed real, gravação no Turso e deduplicação entre execuções independentes comprovadas no conjunto de três itens testado. Homologação operacional manual **APROVADA**; não é prova de execução automática, escala, capacidade editorial, nem produção. Avisos de depreciação Node.js nas Actions não afetaram o resultado; monitorar atualização de checkout/setup-python.

**Restrições preservadas:** sem agendamento, sem deploy, sem redação automática, sem IA e sem WordPress; usar banco `mkt-rss-homolog` apenas para testes, nunca os secrets de produção. Ação manual não deve ser repetida automaticamente. Lease de concorrência de 300s continua sem renovação.

**Próxima fase proposta:** triagem humana de pautas já registradas: listar estado `DESCOBERTA`, exibir metadados e pontuação **heurística**, permitir decisão explícita `SELECIONADA` ou `REJEITADA` com justificativa e auditoria. Não presumir que três pautas homologadas são aprovadas para redação. Contrato e critérios em `docs/RSS_EDITORIAL_TRIAGE_P1_PLAN.md`.
