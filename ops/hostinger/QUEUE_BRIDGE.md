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
- A requisição remota atualmente publicada na branch operacional ainda é `binance-substantive-review-20261114-v2`. Não substituir essa requisição nem sobrescrever seu recibo até confirmar seu estado.
- Portanto, snapshot direto está homologado; o fluxo remoto via controlador e Cron, implantação e coleta continuam pendentes.
