# Hostinger â†” MKT-RSS/Turso: ponte controlada (primeira intervenÃ§Ã£o)

**Escopo:** reutilizar o Cron e o `remote_controller.py` existentes, sem instalar serviÃ§os, criar tabelas ou alterar o WordPress.

## Capacidades

- `queue_snapshot`: lÃª somente `SELECT estado, COUNT(*) FROM rss_pautas GROUP BY estado` no Turso real. NÃ£o chama `fila_pautas.listar()`, pois essa funÃ§Ã£o inicializa tabelas.
- `queue_collect`: coleta **somente Tecnoblog**, atÃ© **2 itens**, pela implementaÃ§Ã£o existente `rss_queue_collect.coletar()`. DeduplicaÃ§Ã£o e lease de um gravador continuam em `fila_pautas`. NÃ£o gera artigos, nÃ£o usa IA, nÃ£o escreve WordPress.
- Antes da coleta, `CONEXO_RSS_SCHEMA_PREEXISTS=1` faz `fila_pautas` verificar as tabelas existentes e bloquear se alguma faltar; nÃ£o executa DDL/migraÃ§Ãµes.
- A ponte reutiliza o arquivo privado existente `~/.config/conexo-os/rss-queue.env` para obter `TURSO_DATABASE_URL` e exige `CONEXO_RSS_TARGET_DB=mkt-rss`. O token Ã© lido do arquivo privado existente `turso-rss-writer.token`. O arquivo .env Ã© analisado por parser restrito da biblioteca padrÃ£o do Python: somente as duas chaves necessÃ¡rias sÃ£o lidas; nÃ£o hÃ¡ execuÃ§Ã£o de shell, interpolaÃ§Ã£o nem dependÃªncia adicional.
- AÃ§Ãµes antigas do artigo Binance sÃ£o preservadas, inclusive o `article_ref` restrito.
- Recibos durÃ¡veis por `job_id` impedem replay e preservam o recibo legado.
- **NÃ£o hÃ¡ execuÃ§Ã£o autÃ´noma da fila por padrÃ£o.** Cada aÃ§Ã£o exige nova requisiÃ§Ã£o explÃ­cita no GitHub e implantaÃ§Ã£o do cÃ³digo confiÃ¡vel na Hostinger.

## PrÃ©-requisitos de runtime (sem credenciais no GitHub)

- CÃ³digo revisado instalado no checkout privado confiÃ¡vel da Hostinger em `~/mkt-rss-runner`.
- `rss-queue.env` pertencente ao usuÃ¡rio, arquivo regular, sem symlink e modo 0600.
- `turso-rss-writer.token` pertencente ao usuÃ¡rio, arquivo regular, sem symlink e permissÃµes 0400/0600.
- Endpoint principal `mkt-rss-*.turso.io`, excluindo homologaÃ§Ã£o; seleÃ§Ã£o explÃ­cita `CONEXO_RSS_TARGET_DB=mkt-rss`.
- O papel do token deve possuir as permissÃµes da aÃ§Ã£o. Se faltar acesso, a tarefa bloqueia, sem fallback SQLite ou elevaÃ§Ã£o de privilÃ©gios.

## Como solicitar uma consulta da fila

ApÃ³s revisÃ£o, integraÃ§Ã£o Ã  branch operacional e implantaÃ§Ã£o controlada do cÃ³digo, criar novo `job_id` no arquivo `ops/hostinger/remote_request.json` da branch `feat/hostinger-runtime-independente-20261113`:

```json
{
  "schema": "conexo-remote-request/1",
  "job_id": "queue-snapshot-20261116-001",
  "action": "queue_snapshot",
  "article_ref": "rss-pautas"
}
```

O Cron atual consulta a requisiÃ§Ã£o a cada cinco minutos; o agendamento nÃ£o prova execuÃ§Ã£o. Verificar recibo e resposta real `PASS` na Hostinger. Para coleta, usar novo `job_id` somente depois da validaÃ§Ã£o de leitura e de autorizaÃ§Ã£o especÃ­fica.

**NÃ£o alterar o pedido ativo da Binance nesta PR** e nÃ£o executar nova coleta antes da autorizaÃ§Ã£o especÃ­fica.

## Testes locais sem rede

```bash
python -m unittest discover -s tests -p test_remote_queue_bridge.py -v
```

Os 11 testes offline cobrem allowlist, vÃ­nculo de referÃªncia, ausÃªncia de credenciais, reutilizaÃ§Ã£o segura do arquivo .env e token existentes, bloqueio de banco nÃ£o principal, URL, permissÃµes, parser sem execuÃ§Ã£o de shell/chaves duplicadas, SELECT somente-leitura, limite de coleta e replay. A execuÃ§Ã£o real de snapshot no Turso confirma conectividade e leitura; nÃ£o certifica ainda o caminho GitHub â†’ Cron â†’ controlador.

## ReversÃ£o

Sem deploy automÃ¡tico nesta entrega. Para reverter apÃ³s futura implantaÃ§Ã£o, restaurar o commit anteriormente confiÃ¡vel do `remote_controller.py` no checkout Hostinger, sem mexer no banco, Cron, Gate ou WordPress. Preservar recibos privados para auditoria; nÃ£o apagar IDs processados para tentar novamente.


## EvidÃªncia de homologaÃ§Ã£o â€” 16/11/2026

- No checkout isolado da Hostinger, `py_compile` passou e os 11 testes passaram (`Ran 11 tests in 0.194s; OK`).
- `remote_queue_bridge.py --snapshot` executado com sucesso contra o Turso principal: `status=PASS`, `mode=READ_ONLY`, `total=18`, com 18 itens em `DESCOBERTA` e zero nos demais estados reportados.
- A leitura nÃ£o alterou WordPress, publicaÃ§Ã£o ou dados da fila.
- O Cron de produÃ§Ã£o permanece `*/5 * * * *` e executa `remote_controller.py` do checkout principal. O comando sÃ³ faz `git pull` se o controlador nÃ£o existir; como ele jÃ¡ existe, merge isolado nÃ£o implanta esta versÃ£o.
- A requisiÃ§Ã£o remota publicada na branch operacional **mudou** em 16/11/2026: o commit `b57503d` (`ops(hostinger): request read-only Turso queue snapshot`) substituiu `binance-substantive-review-20261114-v2` por `queue-snapshot-20261116-001` (`action=queue_snapshot`, `article_ref=rss-pautas`). A afirmaÃ§Ã£o anterior de que a requisiÃ§Ã£o Binance ainda estava publicada estÃ¡ superada. O recibo Binance no Hostinger continua a ser referÃªncia histÃ³rica e precisa ser confirmado, nÃ£o apagado.
- ConsequÃªncia no Cron atual: o `remote_controller.py` instalado ainda exige `article_ref=binance-revisao-6e8da0b05713` e nÃ£o conhece `queue_snapshot`; portanto o Cron falha fechado (`BLOCKED`) ao encontrar a requisiÃ§Ã£o nova, sem escrita em fila, WordPress ou Turso. A requisiÃ§Ã£o sÃ³ passa a ser executada depois da implantaÃ§Ã£o controlada desta PR.
- Ordem de implantaÃ§Ã£o obrigatÃ³ria (evita queimar o `job_id`): validar `remote_queue_bridge.py --snapshot` com o interpretador do virtualenv **antes** de instalar o `remote_controller.py` novo. O controlador novo invoca a ponte por `sys.executable`; se o Cron executar o controlador com um interpretador sem as dependÃªncias do Turso, o job termina `FAILED` e, por design de recibo durÃ¡vel, o `job_id` nÃ£o Ã© repetido â€” seria preciso um `job_id` novo, com nova requisiÃ§Ã£o explÃ­cita.
- Portanto, snapshot direto estÃ¡ homologado; o fluxo remoto via controlador e Cron, implantaÃ§Ã£o e coleta continuam pendentes.


## EvidÃªncia de homologaÃ§Ã£o â€” 16/11/2026 (implantaÃ§Ã£o real e execuÃ§Ã£o pelo Cron)

- **CÃ³digo implantado no checkout da Hostinger** (`~/mkt-rss-runner`), fora de merge, em 16/11 12:45: `ops/hostinger/remote_controller.py` (substituÃ­do) e `ops/hostinger/remote_queue_bridge.py` (novo). Backup do controlador anterior em `~/.local/state/conexo-os/pr123-install-20261116T124522Z/`.
- **Integridade verificada por SHA-256**: os arquivos instalados sÃ£o byte-a-byte iguais aos blobs desta PR â€” `remote_controller.py` = `c2e7250aa65470f0356b9088ef45f8077df68e4372c682a0ca7793a38e519cbb`, `remote_queue_bridge.py` = `99320640daa5d8ca1c5ebca849f8c9ed2bf93d73fd1ca3c2fdb47372cbc6bcef`. Sem adulteraÃ§Ã£o entre revisÃ£o e produÃ§Ã£o.
- **Ponte validada no servidor** com o virtualenv 3.11.18: `remote_queue_bridge.py --snapshot` â†’ `status=PASS`, `mode=READ_ONLY`, `total=18` (18 pautas em `DESCOBERTA`), `wordpress_written=false`, `publication_authorized=false`.
- **Fluxo remoto comprovado por execuÃ§Ã£o manual**: recibo `queue-snapshot-20261116-001.json` â†’ `status=PASS`, `action=queue_snapshot`, `completed_utc=2026-11-16T13:49:00Z`.
- **ExecuÃ§Ã£o autÃ´noma pelo Cron comprovada**: job `queue-snapshot-20261116-002` (commit `7bf70ee` na branch operacional) processado pelo agendador `*/5` da Hostinger em `2026-11-16T16:01:01Z` â†’ `status=PASS`; os ticks seguintes responderam `ALREADY_PROCESSED`, comprovando idempotÃªncia por recibo durÃ¡vel. Recibos gravados com modo `0600` em `~/.local/state/conexo-os/remote-jobs/`.
- **Fila Turso inalterada**: 18 pautas, todas em `DESCOBERTA`, `affected: 0`; nenhuma escrita em fila, WordPress ou Turso em nenhum dos execuÃ§Ãµes.
- **DiagnÃ³stico do Cron**: o agendador do hPanel executa comandos do usuÃ¡rio de forma confiÃ¡vel (sonda repetida: `HOME=/home/u401421381`, `PWD=/home/u401421381`, interpretador `/home/u401421381/mkt-rss-runner/.venv/bin/python` a cada minuto). O campo "Comando para executar" do hPanel tem limite de **255 caracteres** e a tarefa `*/5` original, com comando inline longo, nÃ£o executava e nÃ£o deixava saÃ­da visÃ­vel. **CorreÃ§Ã£o**: o agendador deve chamar um script curto e versionado, nÃ£o um comando inline extenso.
- **Ordem de implantaÃ§Ã£o mantida**: a ponte foi validada antes de instalar o controlador novo, evitando queimar um `job_id` (nÃ£o repetÃ­vel por design).
- Recibo Binance preservado como referÃªncia histÃ³rica: `binance-substantive-review-20261114-v2` â†’ `PASS` em 14/11 17:48Z. PASS de revisÃ£o assistida **nÃ£o** Ã© aprovaÃ§Ã£o humana nem publicaÃ§Ã£o.

### Pendente apÃ³s esta evidÃªncia
- Coleta real (`queue_collect`, Tecnoblog, atÃ© 2 itens) â€” exige autorizaÃ§Ã£o especÃ­fica do proprietÃ¡rio; Ã© escrita no banco.
- ConsolidaÃ§Ã£o: dedupe, lease, reexecuÃ§Ã£o segura e integraÃ§Ã£o MKT-RSS/Turso.
- PublicaÃ§Ã£o, Gate Editorial e WordPress permanecem bloqueados e intocados.

