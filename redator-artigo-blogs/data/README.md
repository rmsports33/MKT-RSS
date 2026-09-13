# data/ — specs verificadas entram AQUI (nunca no código)

- `curated_specs.json` (você cria): lista `[{"modelo": "...", "categoria": "...",
  "specs": {"tela.polegadas": "6.4", ...}, "fonte": "fabricante X"}]`.
  Fonte = ficha do fabricante ou medição própria. Sem entrada aqui, o gerador
  escreve "— não informado" em vez de inventar.
- `search_cache.json`: cache automático da busca (gitignored).
- `redator.db`: rascunhos/histórico local (gitignored).
