# Trilha de execução no caminho real MKT-RSS/Groq

Código proposto: `mkt_flow_p0/editorial_trace.py` + instrumentação de
`rewriter.py` e `pipeline_rss.py`.

## O que está efetivamente ligado nesta branch

- A resposta bem-sucedida de `reescrever_materia` informa o modelo Groq
  observado e SHA-256 do prompt enviado, sem guardar corpo do prompt.
- `processar_item` gera eventos da etapa de geração e registra
  `NOT_RUN`/ `UNKNOWN` para revisão de estilo/SEO/fatos que não possuem
  recibo independente. Nunca fabrica aprovação.
- Quando `--handoff-dir` é utilizado, o CLI grava um arquivo exclusivo
  `trace-<run_id>.json` no mesmo diretório do handoff.
- O resultado WordPress draft só recebe `delivery_readback=PASS`
  quando o adaptador existente retornou rascunho confirmado por readback.
- O importador compartilhado está no Conexo OS PR #51:
  `editorial/trace_ingest.py`, que usa `TraceStore` do mesmo PR.

## Limites operacionais reais (não confundir branch com deploy)

O workflow manual atual `.github/workflows/rss-homolog-manual.yml`
em `master` faz checkout do commit FIXO
`897c38e1fffde6b94608e1f90bd04601b39d6ec8`. Assim, ele
**não executa esta branch**; não alterar o pin sem integração e testes.
O workflow atual carrega somente `output/qa/manifest.json` como artefato
por UM DIA; os sidecars da pasta `output/handoffs` não são
automaticamente preservados após o fim do runner. Para retenção
permanente e compartilhamento entre executores, o próximo passo é
ingestão autenticada em banco central já existente (por exemplo,
Turso), com controle de acesso, idempotência e retenção segura.

Não colocar token, texto completo de artigo, prompt, credenciais ou
conteúdo não publicado em artefatos acessíveis publicamente. O
`editorial_trace` retornado pelo pipeline é metadado operacional;
não implica que um agente do ChatGPT nem um revisor humano tenha
validado o artigo.

## Testes propostos

`python -m unittest discover -s tests -p test_editorial_trace_bridge.py -v`

Sem gasto/deploy. Continuação: Conexo OS issue #50 e PR #51.

## Persistência em Turso (opt-in, reutiliza banco existente)

O módulo `mkt_flow_p0/editorial_trace_turso.py` utiliza
`mkt_flow_p0.cloud_db.turso_execute`, com SQL parametrizado, para criar
uma tabela exclusiva `conexo_editorial_trace_v1` e persistir um pacote
de metadados por `run_id`. A tabela **não foi criada nem acessada no Turso
real nesta entrega**. O executor autenticado cloud pode habilitar:

```sh
python pipeline_rss.py --fonte tecnoblog --limit 1 --handoff-only \
  --handoff-dir output/handoffs --trace-turso
```

São necessários `TURSO_DATABASE_URL` e `TURSO_AUTH_TOKEN` já existentes
e `CONEXO_TRACE_TURSO_ALLOWED_HOST` igual **exatamente** ao hostname do
banco autorizado. Sem correspondência, o módulo não faz requisição.
Não adicionar tokens ao repositório nem executar o comando sem homologação
do banco e quota Free. Uma falha após INSERT pode ser resultado incerto:
consultar `get_turso_trace(run_id)` antes de qualquer nova operação.
O conector WordPress-first no Conexo OS PR #51 tem o mesmo esquema de
persistência para servidores JavaScript, sem exigir Python.

O sincronismo para o núcleo é via envelope `conexo-editorial-executor-events/1`
e `editorial.trace_ingest.ingest_envelope`. Um revisor ainda precisa
vincular o adaptador ao host WordPress MCP; não inferir que o fluxo
ChatGPT-first esteja interceptado automaticamente.

Testes adicionais, criados e ainda não executados:

```sh
python -m unittest discover -s tests -p test_editorial_trace_turso.py -v
```
