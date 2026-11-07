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
