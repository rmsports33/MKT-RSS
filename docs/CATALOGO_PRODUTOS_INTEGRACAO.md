# Catálogo Mestre — integração incremental

O catálogo JSON em `mkt-flow-escrita/pautas/catalogo-produtos.json` contém 18 produtos candidatos. `mkt_flow_p0.product_catalog` oferece correspondência exata e classificação de manchetes. A coleta RSS (`rss_queue_collect.py`) apenas soma contadores de correspondência; não altera o item, a deduplicação RSS, o Turso, o WordPress nem o Gate. Correspondências não são confirmação factual e não liberam publicação.

O catálogo é referência versionada em GitHub, não um segundo banco operacional. Não há sincronização bidirecional implementada. A revisão do PR e execução dos testes precedem merge. Integração de variantes/SKU e deduplicação semântica da fila real permanecem pendentes.

## Triagem sem franquias
Para avaliar uma lista nova, salve um JSON de strings (ex.: `["TCL C6K 55", "Produto novo"]`) e execute da raiz do repositório:

```sh
python -m scripts.product_catalog_triage produtos-novos.json --output triagem.json
```

`EXISTS` aponta o cadastro existente; `NEW_CANDIDATE` requer curadoria; `REVIEW` é ambiguidade/entrada inválida. O comando não grava no catálogo, não chama IA, Turso, WordPress, GitHub API ou Actions. Nenhum resultado autoriza publicação. Não versionar arquivos de entrada que contenham dados privados.

## Política de custos e implantação
- Catálogo JSON versionado no repositório é a fonte oficial dos produtos, não a fila editorial.
- A classificação na coleta RSS é auxiliar, sem escrita de produtos no Turso.
- Evitar consultas ao Turso por produto e novas rotinas agendadas.
- GitHub Actions existente pode rodar testes quando houver alteração; a triagem em lote não exige workflow.
- Para relacionar pauta a artigo, exigir checagem independente de estado editorial e aprovação pelo Gate Único.

## Evidência de homologação RSS real — 2026-11-13

- Execução no GitHub Actions (runner com rede): https://github.com/rmsports33/MKT-RSS/actions/runs/43418460117
- Comando executado: `python rss_queue_collect.py --fonte gsmarena --limit 10 --dry-run`.
- Resultado capturado do log: `{"analisadas":10,"catalogo":{"correspondencias":1,"revisao":0,"sem_correspondencia":9},"duplicadas":0,"falhas":[],"fora_da_janela":0,"modo":"DIAGNOSTICO_SEM_ESCRITA","novas":0}`.
- Testes na mesma execução: `1241 passed, 1 skipped, 13 subtests passed` na suíte principal e `52 passed` no redator.
- Diagnóstico sem credenciais remotas; `registrar` não é executado em `--dry-run`. Portanto **nenhuma escrita foi solicitada** à fila e nenhum teste de escrita real no Turso foi realizado.
- A etapa temporária foi removida do CI após a coleta da evidência, sem criar workflow agendado ou gasto recorrente.
- **Escopo homologado:** acesso ao RSS real, parsing, janela temporal, classificação do catálogo e saída JSON coerente, com testes que impedem chamadas a `registrar` no modo diagnóstico.
- **Não homologado aqui:** persistência autenticada do Turso na coleta normal, reconciliar toda a fila histórica e liberação de publicação WordPress. Essas operações exigem validação separada e não são pré-requisitos para triagem offline.
