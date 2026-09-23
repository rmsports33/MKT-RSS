# Pacote OpenCode — pesquisa turbinada (instalar uma vez)

O que já existe aí (verificado, não mexi): `/pesquisar`, `instructions/pesquisa-web.md`,
skill `programmatic-seo`, permissão websearch/webfetch liberada. Isto aqui COMPLETA:

| Arquivo | Instalar em | O que ganha |
|---|---|---|
| `agents/pesquisador.md` | `~/.config/opencode/agents/` | Subagente só-pesquisa (sem editar nada), chamável com `@pesquisador` ou via Task em paralelo |
| `skills/pesquisa-conexotech/SKILL.md` | `~/.config/opencode/skills/` | Protocolo comercial (claims A–E, disclosure, placeholders) sob demanda em qualquer sessão |
| `opencode-mcp-snippet.jsonc` | Mesclar no seu `opencode.jsonc` | Ferramentas Exa nativas (busca semântica + contents + crawl). Exige Node/npx + `EXA_API_KEY` no ambiente |

## Instalação (5 min)

1. Copie as pastas `agents/` e `skills/` para dentro de `~/.config/opencode/`.
2. No seu `opencode.jsonc`, adicione o bloco `mcp` do snippet (se já houver `mcp`, funda as chaves).
3. Garanta `EXA_API_KEY` no ambiente (mesma chave do `.env`; nunca colar no chat).
4. **Reinicie o opencode** (MCP só carrega no boot). Confira com `opencode mcp list`.
5. Use: `@pesquisador ficha oficial Galaxy A54 Brasil` ou peça "pesquisa em paralelo" que eu divido em subagentes.

## Avisos honestos

- MCP come contexto (doc oficial alerta): se a sessão ficar pesada, desative com `"enabled": false`.
- Confirme o nome do pacote Exa (`exa-mcp-server`) na doc deles na hora de instalar.
- Chave Exa continua na cota grátis (US$20 + US$10/mês); monitore o consumo no dashboard deles.
- Nada aqui substitui o gate humano antes de publicar.
