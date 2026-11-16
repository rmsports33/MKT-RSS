# Hostinger ↔ MKT-RSS/Turso: ponte controlada (primeira intervenção)

**Escopo:** reutilizar o Cron e o `remote_controller.py` existentes, sem instalar serviços, criar tabelas ou alterar o WordPress.

## Capacidades

- `queue_snapshot`: lê somente `SELECT estado, COUNT(*) FROM rss_pautas GROUP BY estado` no Turso real. Não chama `fila_pautas.listar()`, pois essa função inicializa tabelas.
- `queue_collect`: coleta **somente Tecnoblog**, até **2 itens**, pela implementação existente de `rss_queue_collect.coletar()`. Deduplicação e lease de um gravador continuam em `fila_pautas`. Não gera artigos, não usa IA, não escreve WordPress.
- Antes da coleta, `CONEXO_RSS_SCHEMA_PREEXISTS=1` força `fila_pautas` a verificar as tabelas já existentes e bloqueia se alguma faltar; não executa DDL/migrações.
- Ações antigas do artigo Binance são preservadas, inclusive o `article_ref` restrito.
- Toda requisição tem `job_id` único; recibos em `~/.local/state/conexo-os/remote-jobs/<job_id>.json` impedem replay. O recibo legado é migrado para impedir que o pedido atual execute outra vez.
- **Não há execução autônoma da fila por padrão.** Cada ação exige nova requisição explícita no GitHub e implantação do código confiável na Hostinger.

## Pré-requisitos de runtime (sem credenciais no GitHub)

- Código revisado instalado no checkout privado confiável da Hostinger em `~/mkt-rss-runner`.
- `TURSO_DATABASE_URL` no ambiente do processo ou arquivo local `~/.config/conexo-os/turso-database-url` pertencente ao usuário e com permissões 0600.
- Token **já existente** `~/.config/conexo-os/turso-rss-writer.token` pertencente ao usuário e com permissões 0400 ou 0600. Não revelar, copiar para GitHub, imprimir ou pedir em chat.
- URL HTTPS/libsql restrita ao banco principal `mkt-rss-*.turso.io`, excluindo URLs de homologação.
- O papel do token deve possuir permissões para a ação. Se faltar qualquer acesso, a tarefa bloqueia, sem fallback SQLite ou elevação de privilégios.

## Como solicitar uma consulta da fila

Depois de revisão, integração à branch operacional e implantação controlada do código, criar **novo** `job_id` no arquivo já existente `ops/hostinger/remote_request.json` da branch **`feat/hostinger-runtime-independente-20261113`**:

```json
{
  "schema": "conexo-remote-request/1",
  "job_id": "queue-snapshot-20261115-001",
  "action": "queue_snapshot",
  "article_ref": "rss-pautas"
}
```

O Cron atual consulta a requisição a cada cinco minutos, mas **o agendamento não é prova de execução bem-sucedida**. Verificar o recibo e uma resposta `PASS` no Hostinger. Para coleta, usar novo `job_id` e `action=queue_collect` após validação de leitura e permissões adequadas.

**Não alterar o pedido ativo da Binance nesta PR** e não executar uma nova coleta antes do aceite específico.

## Testes locais sem rede

```bash
python -m unittest discover -s tests -p test_remote_queue_bridge.py -v
```

Os testes cobrem allowlist, vínculo de referência, ausência de credenciais, configuração fail-closed de schema preexistente, URL, permissões de arquivo, SELECT somente-leitura, limite de coleta e replay do recibo anterior. Testes mockados **não** certificam conexão Turso nem execução do Cron.

## Reversão

Sem deploy automático nesta entrega. Para reverter após futura implantação, restaurar o commit anteriormente confiável do `remote_controller.py` no checkout Hostinger, sem mexer no banco, Cron, Gate ou WordPress. Os recibos privados podem ser preservados para auditoria; não apagar IDs processados com o objetivo de tentar novamente.
