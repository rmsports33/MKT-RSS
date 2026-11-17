# M14 — Auditoria de preços publicados — 17/11/2026

Somente leitura: 12 URLs com preço conferidas, nenhuma alteração no site.
Ferramenta reaproveitável: `tools/auditar_precos_publicados.py`.

## Resultado

Limite de referência: 30 dias. Hoje: 17/11/2026.

| Situação | Qtd |
|---|---|
| Desatualizado (> 30 dias) | 10 |
| Sem data de captura | 2 |
| Em dia | 0 |
| **Total com preço** | **12** |

| Página | Idade da captura | Situação |
|---|---|---|
| `/galaxy-watch-9-ultra-2-precos-brasil/` | 103 dias | desatualizado |
| `/iphone-18-pro-brasil-precos-disponibilidade/` | 60 dias | desatualizado |
| `/reviews/galaxy-s26-ultra-review/` | 52 dias | desatualizado |
| `/reviews/galaxy-a37-5g-256-gb-preco-caiu-para-r-1-709-capturado-em-17-09/` | 52 dias | desatualizado |
| `/` (home) | 51 dias | desatualizado |
| `/reviews/` (listagem) | 51 dias | desatualizado |
| `/reviews/iphone-17e-256-gb-...-capturado-em-27-09-2026/` | 51 dias | desatualizado |
| `/reviews/tcl-50p7l-qled-50-polegadas-analise/` | 51 dias | desatualizado |
| `/reviews/samsung-galaxy-a57-5g-vale-a-pena-em-2026/` | 46 dias | desatualizado |
| `/redmi-watch-6-lite-active-brasil-preco/` | 42 dias | desatualizado |
| `/guia-airpods-2026/` | — | sem data |
| `/binance-ataque-hacker-636-bilhoes-coreia-do-norte/` | — | sem data |

## Leitura do resultado

- **Nenhum preço está dentro da janela de 30 dias.** O mais recente tem 42 dias.
- Dois casos são piores que "desatualizado": exibem valor **sem data de captura**,
  o que contraria a regra do projeto (preço sempre com data, mercado e variante).
- `home` e `/reviews/` não são artigos: herdam a data do que exibem. Corrigir os
  artigos corrige as listagens.
- Dois títulos carregam a data no próprio slug (`capturado em 27-09-2026`,
  `capturado em 17-09`). Se o preço for atualizado, o slug fica contraditório —
  decidir: manter URL antiga (preserva SEO) ou redirecionar.

## O que eu não fiz

Não alterei preço, não reescrevi artigo, não troquei imagem. Preço sem fonte
datada é invenção — e o projeto proíbe isso. A correção exige nova captura em
marketplace, com data e link.

## Próximo passo sugerido

1. Escolher 3 páginas de maior tráfego (sugestão: `galaxy-s26-ultra`,
   `iphone-18-pro`, `galaxy-watch-9-ultra-2`).
2. Coletar preço novo com data e link de oferta.
3. Atualizar o artigo por versão, com readback — não em massa.

## Como repetir a auditoria

```
python tools/auditar_precos_publicados.py --dias 30
python tools/auditar_precos_publicados.py --json   # saída completa com os valores
```
