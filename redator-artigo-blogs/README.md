# redator-artigo-blogs — Comparativos com specs verificadas

Gerador de artigos comparativos (celular, notebook, TV...) a partir de fichas
técnicas **fornecidas por você**. Cadeia 100% gratuita: OpenRouter (Gemini free)
→ Ollama local. Sem chave paga em nenhum ponto.

## Regras anti-invenção (automáticas)
1. Só entra no texto o que está em `specs_PASS` (ficha verificada).
2. Sem ficha → "— não informado", nunca chute.
3. Nenhuma alegação de teste de bancada/uso real (removida se a IA escrever).
4. Números do texto são checados contra as specs (`suspeitas_hallucination`).
5. Citação `[fonte: X]` só de fonte da entrada.

## Uso
1. Copie `.env.example` para `.env` e preencha (OpenRouter e/ou Ollama).
2. Cadastre as fichas em `data/curated_specs.json` (ficha do fabricante).
3. Gere via `src.generator.render.gerar_comparativo(...)` ou peça o roteiro.
4. Saída: HTML pronto (meta + JSON-LD + tabela + gráfico de preço +
   slots AdSense) + auditoria JSON.

> Reconstruído em 12/09/2026 após incidente de disco (ver
> `RESTAURACAO_2026-09-12.md` na raiz): funcionalmente equivalente ao
> original, validado por testes mockados. Geração real exige `.env`.
