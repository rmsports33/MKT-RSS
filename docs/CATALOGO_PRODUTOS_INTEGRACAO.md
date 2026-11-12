# Catálogo Mestre — integração incremental

O catálogo JSON em `mkt-flow-escrita/pautas/catalogo-produtos.json` contém 18 produtos candidatos. `mkt_flow_p0.product_catalog` oferece correspondência exata e classificação de manchetes. A coleta RSS (`rss_queue_collect.py`) apenas soma contadores de correspondência; não altera o item, a deduplicação RSS, o Turso, o WordPress nem o Gate. Correspondências não são confirmação factual e não liberam publicação.

O catálogo é referência versionada em GitHub, não um segundo banco operacional. Não há sincronização bidirecional implementada. A revisão do PR e execução dos testes precedem merge. Integração de variantes/SKU e deduplicação semântica da fila real permanecem pendentes.
