<!-- Status consolidado: docs/REGISTRO_UNICO_20261118.md -->

# M14 â€” Auditoria de preÃ§os publicados â€” 17/11/2026

Somente leitura: 12 URLs com preÃ§o conferidas, nenhuma alteraÃ§Ã£o no site.
Ferramenta reaproveitÃ¡vel: `tools/auditar_precos_publicados.py`.

## Resultado

Limite de referÃªncia: 30 dias. Hoje: 17/11/2026.

| SituaÃ§Ã£o | Qtd |
|---|---|
| Desatualizado (> 30 dias) | 10 |
| Sem data de captura | 2 |
| Em dia | 0 |
| **Total com preÃ§o** | **12** |

| PÃ¡gina | Idade da captura | SituaÃ§Ã£o |
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
| `/guia-airpods-2026/` | â€” | sem data |
| `/binance-ataque-hacker-636-bilhoes-coreia-do-norte/` | â€” | sem data |

## Leitura do resultado

- **Nenhum preÃ§o estÃ¡ dentro da janela de 30 dias.** O mais recente tem 42 dias.
- Dois casos sÃ£o piores que "desatualizado": exibem valor **sem data de captura**,
  o que contraria a regra do projeto (preÃ§o sempre com data, mercado e variante).
- `home` e `/reviews/` nÃ£o sÃ£o artigos: herdam a data do que exibem. Corrigir os
  artigos corrige as listagens.
- Dois tÃ­tulos carregam a data no prÃ³prio slug (`capturado em 27-09-2026`,
  `capturado em 17-09`). Se o preÃ§o for atualizado, o slug fica contraditÃ³rio â€”
  decidir: manter URL antiga (preserva SEO) ou redirecionar.

## O que eu nÃ£o fiz

NÃ£o alterei preÃ§o, nÃ£o reescrevi artigo, nÃ£o troquei imagem. PreÃ§o sem fonte
datada Ã© invenÃ§Ã£o â€” e o projeto proÃ­be isso. A correÃ§Ã£o exige nova captura em
marketplace, com data e link.

## PrÃ³ximo passo sugerido

1. Escolher 3 pÃ¡ginas de maior trÃ¡fego (sugestÃ£o: `galaxy-s26-ultra`,
   `iphone-18-pro`, `galaxy-watch-9-ultra-2`).
2. Coletar preÃ§o novo com data e link de oferta.
3. Atualizar o artigo por versÃ£o, com readback â€” nÃ£o em massa.

## Como repetir a auditoria

```
python tools/auditar_precos_publicados.py --dias 30
python tools/auditar_precos_publicados.py --json   # saÃ­da completa com os valores
```
