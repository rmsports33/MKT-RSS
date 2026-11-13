# Independência do GitHub Actions — executor MKT-RSS na Hostinger (P0)
Data: 13/11/2026 — branch isolada, SEM deploy nem Cron ativado.

## Decisão técnica após inspeção do código real
O GitHub Actions diário atual (`.github/workflows/daily.yml`, master) executa exclusivamente
`python pipeline_rss.py --queue-only --fonte tecnoblog --limit 2`, Python 3.11,
com `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN` e `CONEXO_PRODUCT_LINKS_ENABLED=1`.
O MKT-RSS já inclui o contrato de `fila_pautas.registrar`, pontuação e
`rss_queue_mutex` single-writer. Reimplementar em PHP traria divergência desnecessária.
O novo `ops/hostinger/run_rss_queue.sh` reutiliza o motor atual,
não gera artigos, não chama IA, não cria rascunhos WordPress e não publica.

## Pré-requisitos (pendentes de prova no servidor)
- Checkout MKT-RSS em pasta privada de HOME **fora de public_html**; nunca deploy por FTP na produção.
- Python 3.11–3.14 e dependências RSS em virtualenv privado. Hostinger SSH tem
  Python 3.6.8, que **não pode** executar o pipeline; usar um runtime privado compatível
  somente se instalação for permitida pelo ambiente. Não mudar o Python do sistema.
- `flock` do Linux disponível; sem ele o runner bloqueia.
- Ambiente secreto `~/.config/conexo-os/rss-queue.env`, propriedade do usuário,
  permissão 0600, criado em sessão autenticada. Não commitar e não mostrar no chat.
- URL de Turso main (NÃO homolog), credencial de banco com privilégios mínimos.
  Token de autenticação da **plataforma Turso CLI** não deve ser reutilizado no pipeline
  como se fosse token de banco. Evitar WordPress, Groq e outros secrets no processo.
- **Não** habilitar Cron antes de desabilitar o agendamento equivalente no Actions.

## Exemplo de chaves no arquivo privado (placeholders, não são segredos)
```bash
TURSO_DATABASE_URL='libsql://mkt-rss-ACCOUNT.REGION.turso.io'
TURSO_AUTH_TOKEN='REPLACE_LOCALLY_WITH_DATABASE_TOKEN'
CONEXO_RSS_TARGET_DB='mkt-rss'
CONEXO_PRODUCT_LINKS_ENABLED=1
CONEXO_RSS_LIMIT=2
CONEXO_RSS_CRON_ACTIVE=0
CONEXO_RSS_WRITER_OWNER=none
CONEXO_ACTIONS_WRITER_DISABLED=0
```
Lembrar: `TURSO_AUTH_TOKEN` do MKT-RSS é token de acesso SQL ao banco,
não `turso config set token` (token de conta administrativa).
Para criar arquivo, use editor privado; depois `chmod 600` nele.
Não colocar credenciais em variáveis de cron, URL pública, repositório ou log.

## Testes antes de autorizar escritas
```bash
export CONEXO_RUNNER_ROOT="$HOME/mkt-rss-runner"
export CONEXO_PYTHON="$CONEXO_RUNNER_ROOT/.venv/bin/python"
bash "$CONEXO_RUNNER_ROOT/ops/hostinger/run_rss_queue.sh" --preflight
```
O `--preflight` testa instalação e configuração e **não** toca banco, rede RSS ou WP.
Apenas com o runtime válido: testar coleta sem escrita em `rss_shadow_probe.php`
(pode depender da extensão SimpleXML). Comparar feeds, títulos e URLs com o MKT-RSS
Python; não registrar conteúdo novo no banco de produção durante o shadow.

## Cutover supervisionado (NÃO executado)
1. Confirmar backup Turso autenticado recuperável, logs, versão do checkout,
   unicidade da fila e equivalência dos dados de shadow.
2. Desabilitar **somente o gatilho `schedule`** de `.github/workflows/daily.yml`
   em master, preservando `workflow_dispatch` para emergências e demais CI;
   verificar que alteração foi implantada e que não há run diário ainda ativo.
   Não mexer em workflows de SEO/Gate/publicação.
3. Em arquivo privado, ajustar `CONEXO_ACTIONS_WRITER_DISABLED=1`,
   `CONEXO_RSS_WRITER_OWNER=hostinger`, `CONEXO_RSS_CRON_ACTIVE=1`;
   esses flags são declarações operacionais, não verificações automáticas de GitHub.
4. Rodar **um** `--run` manual; confirmar JSON, linha SUCCESS, e readback idempotente
   em `rss_pautas`/Turso. Falha aborta sem reativar segundo writer concorrente.
5. Só então configurar 1 Cron Hostinger, apontando para wrapper privado,
   por exemplo (ilustrativo; caminhos e timezone devem ser confirmados):
   `/bin/bash /home/USER/mkt-rss-runner/ops/hostinger/run_rss_queue.sh --run`.
   Cron sem os exports necessários do `CONEXO_RUNNER_ROOT` não funcionará;
   usar wrapper privado que exporta somente ROOT/PYTHON e executa o runner,
   protegido e fora public_html. Nunca deixar segredos em argumentos de cron.
6. Confirmar 2-3 execuções, tempo real de execução, logs sem secrets, contagens
   e ausência de execuções Actions. Adicionar watchdog para última coleta bem-sucedida.
7. No rollback, **desativar Cron primeiro** e aguardar não haver execução ativa;
   só então restaurar schedule Actions se explicitamente autorizado.
   Nunca deixar dois escritores ativos.

## Estado verificável após esta entrega
- Arquivos em branch GitHub, sem merge, CI completa, instalação Hostinger,
  credenciais privadas, preflight real ou escrita em Turso.
- As URLs de read-only PHP são sondas auxiliares; **não** são o novo pipeline.
- Dependência real de GitHub Actions permanece ATIVA até cutover controlado.
- Nenhum impacto em WordPress, Turso, Hostinger Cron e Gate nesta etapa.
