# Hostinger ↔ MKT-RSS/Turso: ponte controlada (primeira intervenção)

**Escopo:** reutilizar o Cron e o `remote_controller.py` existentes, sem instalar serviços, criar tabelas ou alterar o WordPress.

## Capacidades

- `queue_snapshot`: lê somente `SELECT estado, COUNT(*) FROM rss_pautas GROUP BY estado` no Turso real. Não chama `fila_pautas.listar()`, pois essa função inicializa tabelas.
- `queue_collect`: coleta **somente Tecnoblog**, até **2 itens**, pela implementação existente `rss_queue_collect.coletar()`. Deduplicação e lease de um gravador continuam em `fila_pautas`. Não gera artigos, não usa IA, não escreve WordPress.
- Antes da coleta, `CONEXO_RSS_SCHEMA_PREEXISTS=1` faz `fila_pautas` verificar as tabelas existentes e bloquear se alguma faltar; não executa DDL/migrações.
- A ponte reutiliza o arquivo privado existente `~/.config/conexo-os/rss-queue.env` para obter `TURSO_DATABASE_URL` e exige `CONEXO_RSS_TARGET_DB=mkt-rss`. O token é lido do arquivo privado existente `turso-rss-writer.token`. O arquivo .env é analisado por parser restrito da biblioteca padrão do Python: somente as duas chaves necessárias são lidas; não há execução de shell, interpolação nem dependência adicional.
- Ações antigas do artigo Binance são preservadas, inclusive o `article_ref` restrito.
- Recibos duráveis por `job_id` impedem replay e preservam o recibo legado.
- **Não há execução autônoma da fila por padrão.** Cada ação exige nova requisição explícita no GitHub e implantação do código confiável na Hostinger.

## Pré-requisitos de runtime (sem credenciais no GitHub)

- Código revisado instalado no checkout privado confiável da Hostinger em `~/mkt-rss-runner`.
- `rss-queue.env` pertencente ao usuário, arquivo regular, sem symlink e modo 0600.
- `turso-rss-writer.token` pertencente ao usuário, arquivo regular, sem symlink e permissões 0400/0600.
- Endpoint principal `mkt-rss-*.turso.io`, excluindo homologação; seleção explícita `CONEXO_RSS_TARGET_DB=mkt-rss`.
- O papel do token deve possuir as permissões da ação. Se faltar acesso, a tarefa bloqueia, sem fallback SQLite ou elevação de privilégios.

## Como solicitar uma consulta da fila

Após revisão, integração à branch operacional e implantação controlada do código, criar novo `job_id` no arquivo `ops/hostinger/remote_request.json` da branch `feat/hostinger-runtime-independente-20261113`:

```json
{
  "schema": "conexo-remote-request/1",
  "job_id": "queue-snapshot-20261116-001",
  "action": "queue_snapshot",
  "article_ref": "rss-pautas"
}
```

O Cron atual consulta a requisição a cada cinco minutos; o agendamento não prova execução. Verificar recibo e resposta real `PASS` na Hostinger. Para coleta, usar novo `job_id` somente depois da validação de leitura e de autorização específica.

**Não alterar o pedido ativo da Binance nesta PR** e não executar nova coleta antes da autorização específica.

## Testes locais sem rede

```bash
python -m unittest discover -s tests -p test_remote_queue_bridge.py -v
```

Os 11 testes offline cobrem allowlist, vínculo de referência, ausência de credenciais, reutilização segura do arquivo .env e token existentes, bloqueio de banco não principal, URL, permissões, parser sem execução de shell/chaves duplicadas, SELECT somente-leitura, limite de coleta e replay. A execução real de snapshot no Turso confirma conectividade e leitura; não certifica ainda o caminho GitHub → Cron → controlador.

## Reversão

Sem deploy automático nesta entrega. Para reverter após futura implantação, restaurar o commit anteriormente confiável do `remote_controller.py` no checkout Hostinger, sem mexer no banco, Cron, Gate ou WordPress. Preservar recibos privados para auditoria; não apagar IDs processados para tentar novamente.


## Evidência de homologação — 16/11/2026

- No checkout isolado da Hostinger, `py_compile` passou e os 11 testes passaram (`Ran 11 tests in 0.194s; OK`).
- `remote_queue_bridge.py --snapshot` executado com sucesso contra o Turso principal: `status=PASS`, `mode=READ_ONLY`, `total=18`, com 18 itens em `DESCOBERTA` e zero nos demais estados reportados.
- A leitura não alterou WordPress, publicação ou dados da fila.
- O Cron de produção permanece `*/5 * * * *` e executa `remote_controller.py` do checkout principal. O comando só faz `git pull` se o controlador não existir; como ele já existe, merge isolado não implanta esta versão.
- A requisição remota publicada na branch operacional **mudou** em 16/11/2026: o commit `b57503d` (`ops(hostinger): request read-only Turso queue snapshot`) substituiu `binance-substantive-review-20261114-v2` por `queue-snapshot-20261116-001` (`action=queue_snapshot`, `article_ref=rss-pautas`). A afirmação anterior de que a requisição Binance ainda estava publicada está superada. O recibo Binance no Hostinger continua a ser referência histórica e precisa ser confirmado, não apagado.
- Consequência no Cron atual: o `remote_controller.py` instalado ainda exige `article_ref=binance-revisao-6e8da0b05713` e não conhece `queue_snapshot`; portanto o Cron falha fechado (`BLOCKED`) ao encontrar a requisição nova, sem escrita em fila, WordPress ou Turso. A requisição só passa a ser executada depois da implantação controlada desta PR.
- Ordem de implantação obrigatória (evita queimar o `job_id`): validar `remote_queue_bridge.py --snapshot` com o interpretador do virtualenv **antes** de instalar o `remote_controller.py` novo. O controlador novo invoca a ponte por `sys.executable`; se o Cron executar o controlador com um interpretador sem as dependências do Turso, o job termina `FAILED` e, por design de recibo durável, o `job_id` não é repetido — seria preciso um `job_id` novo, com nova requisição explícita.
- Portanto, snapshot direto está homologado; o fluxo remoto via controlador e Cron, implantação e coleta continuam pendentes.

# Hostinger ↔ MKT-RSS/Turso: ponte controlada (primeira intervenção)

## Evidência de homologação — 16/11/2026 (implantação real e execução pelo Cron)

- **Código implantado no checkout da Hostinger** (`~/mkt-rss-runner`), fora de merge, em 16/11 12:45: `ops/hostinger/remote_controller.py` (substituído) e `ops/hostinger/remote_queue_bridge.py` (novo). Backup do controlador anterior em `~/.local/state/conexo-os/pr123-install-20261116T124522Z/`.
- **Integridade verificada por SHA-256**: os arquivos instalados são byte-a-byte iguais aos blobs desta PR — `remote_controller.py` = `c2e7250aa65470f0356b9088ef45f8077df68e4372c682a0ca7793a38e519cbb`, `remote_queue_bridge.py` = `99320640daa5d8ca1c5ebca849f8c9ed2bf93d73fd1ca3c2fdb47372cbc6bcef`. Sem adulteração entre revisão e produção.
- **Ponte validada no servidor** com o virtualenv 3.11.18: `remote_queue_bridge.py --snapshot` → `status=PASS`, `mode=READ_ONLY`, `total=18` (18 pautas em `DESCOBERTA`), `wordpress_written=false`, `publication_authorized=false`.
- **Fluxo remoto comprovado por execução manual**: recibo `queue-snapshot-20261116-001.json` → `status=PASS`, `action=queue_snapshot`, `completed_utc=2026-11-16T13:49:00Z`.
- **Execução autônoma pelo Cron comprovada**: job `queue-snapshot-20261116-002` (commit `7bf70ee` na branch operacional) processado pelo agendador `*/5` da Hostinger em `2026-11-16T16:01:01Z` → `status=PASS`; os ticks seguintes responderam `ALREADY_PROCESSED`, comprovando idempotência por recibo durável. Recibos gravados com modo `0600` em `~/.local/state/conexo-os/remote-jobs/`.
- **Fila Turso inalterada**: 18 pautas, todas em `DESCOBERTA`, `affected: 0`; nenhuma escrita em fila, WordPress ou Turso em nenhuma das execuções.
- **Diagnóstico do Cron**: o agendador do hPanel executa comandos do usuário de forma confiável (sonda repetida: `HOME=/home/u401421381`, `PWD=/home/u401421381`, interpretador `/home/u401421381/mkt-rss-runner/.venv/bin/python` a cada minuto). O campo "Comando para executar" do hPanel tem limite de **255 caracteres** e a tarefa `*/5` original, com comando inline longo, não executava e não deixava saída visível. **Correção**: o agendador deve chamar um script curto e versionado, não um comando inline extenso.
- **Ordem de implantação mantida**: a ponte foi validada antes de instalar o controlador novo, evitando queimar um `job_id` (não repetível por design).
- Recibo Binance preservado como referência histórica: `binance-substantive-review-20261114-v2` → `PASS` em 14/11 17:48Z. PASS de revisão assistida **não** é aprovação humana nem publicação.

### Pendente após esta evidência
- Coleta real (`queue_collect`, Tecnoblog, até 2 itens) — exige autorização específica do proprietário; é escrita no banco.
- Consolidação: dedupe, lease, reexecução segura e integração MKT-RSS/Turso.
- Publicação, Gate Editorial e WordPress permanecem bloqueados e intocados.
