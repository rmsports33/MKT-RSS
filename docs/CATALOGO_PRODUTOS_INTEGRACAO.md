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
