# Checkpoint 2026-11-13 — migração MKT-RSS / Hostinger / Turso

Status: **NÃO CONCLUÍDO — implantação desativada intencionalmente**.
Fonte: resultados de execução enviados pelo operador pelo SSH da Hostinger em 2026-11-13.
Este checkpoint não substitui logs externos e não autoriza cortes ou publicações.

## Execuções confirmadas

1. Runtime privado em `$HOME/mkt-rss-runner`, fora de `public_html`, Python 3.11.18 no venv. Coleta `rss_queue_collect.py --fonte tecnoblog --limit 2 --dry-run` aprovada anteriormente, sem escrita.
2. Token de leitura Turso: `TURSO_READ_OK`. Token **restrito de escrita** criado no arquivo privado `$HOME/.config/conexo-os/turso-rss-writer.token` com expiração **7 dias a partir da criação**; não versionar nem publicar segredo.
3. `run_rss_queue.sh --preflight`: `PASS: private runner prerequisites and configuration checks; no network/write performed`.
4. `run_rss_queue.sh --run` sem ativação: `BLOCKED: schedule not activated` (esperado). Cron **não ativado**; GitHub Actions continua sendo o escritor agendado.
5. `test_hostinger_no_schema_writes.py`: 4 testes, `OK`. Runtime endurecido usa `CONEXO_RSS_SCHEMA_PREEXISTS=1`, consulta as tabelas já existentes e não solicita DDL.
6. `test_hostinger_queue_idempotency.py`: 2 testes, `OK`. Comprova idempotência e mutex **em SQLite temporário**, não no Turso.
7. Token restrito contra Turso principal: `WRITER_TOKEN_READ_OK` (read-only probe com o token de escrita).
8. `probe_writer_rollback.py`: bug inicial de import corrigido no commit `773311a`. Execução posterior com `CONEXO_RSS_PERMISSIONS_PROBE=YES_ROLLBACK_ONLY` retornou:
   `{"status":"PASS","proof":"INSERT_WITH_ROLLBACK","persisted_test_rows":0,"wordpress_modified":false,"publication_authorized":false}`.
   Prova: INSERT autorizado em transação, ROLLBACK e consulta independente que retornou zero registros. **Não é prova de inserção permanente nem de execução real do pipeline**.
9. Sem alterações no WordPress, Gate Editorial ou publicação; GitHub Actions ainda não desativado; Cron Hostinger ainda não ativado.

## Pendências restantes, em ordem segura

1. **Revisar antes de novas escritas** o token mínimo e o mecanismo `rss_queue_mutex` real, inclusive `INSERT ... ON CONFLICT DO UPDATE`, `DELETE`, contagem de linhas e falha fechada sob contenda. Testar sobre o Turso de homologação com credencial separada e autorização explícita, ou prova reversível não destrutiva e segura; não correr escritor paralelo sobre o banco principal.
2. **Confirmar esquema existente** de `rss_pautas`, `rss_notas_editoriais`, `rss_queue_mutex` e `rss_product_links` para modo endurecido; validar sucesso da operação opcional de vínculo `rss_product_links` ou falha segura.
3. **Provar idempotência no Turso real** e leitura posterior com a mesma URL; preferir banco `mkt-rss-homolog`, isolado, sem escrever pautas falsas na produção. Executar regressões do pipeline e preflight.
4. **Resolver expiração de sete dias** do token de escrita (rotina de rotação/renovação segura e armazenamento privado com modo 600; sem expor credenciais em logs, chat ou repositório); não usar token de conta administrativa como substituto permanente.
5. **Verificar workflow agendado** em `.github/workflows/daily.yml` e execuções ativas; interromper a posse de escrita pelo GitHub Actions de forma verificável antes de eleger Hostinger. Não tratar edição do workflow como prova de que nenhum job está rodando.
6. Configurar e validar o **Cron na Hostinger** (equivalência de horário do schedule 12:00 UTC; timezone de ambiente), caminho absoluto do runner, ambiente privado, `flock`, logs de retorno, monitoramento de falhas, parâmetros `CONEXO_RSS_CRON_ACTIVE`, `CONEXO_RSS_WRITER_OWNER`, `CONEXO_ACTIONS_WRITER_DISABLED` somente depois do corte comprovado. Evitar dois escritores.
7. Executar **uma coleta queue-only real**, confirmar registros/duplicações e readback no Turso, examinar log sem segredos; testar segunda execução idempotente e recuperação de falha. Só então declarar independência operacional.
8. Registrar os resultados finais no GitHub; preservar WordPress/Gate, não autorizar publicação, não gastar nem depender de GitHub Actions para novas coletas.
9. Backups: os seis Git bundles e dumps SQL das bases Turso estão verificados localmente; permanecem pendentes teste de restauração isolada e eventual cópia externa integral do pacote, sem duplicar desnecessariamente UpdraftPlus/Drive. Não bloquear a migração RSS por auditorias de backup alheias à segurança do corte.

## Retomada

A primeira ação amanhã deve ser uma **inspeção sem escrita do mutex no Turso e preparação de teste seguro de concorrência**. Nenhum comando de ativação Cron/GitHub Actions deve ser emitido até prova do esquema, mutex real e estratégia de rotação de token. Não repetir testes aprovados sem alteração de código relevante.
