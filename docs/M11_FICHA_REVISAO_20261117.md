# M11 — Ficha de revisão do artigo Binance — 17/11/2026

Preparado para reduzir a revisão humana ao mínimo necessário. **Nada foi
publicado, aprovado ou alterado.** Pacote `a80b3e398683cb6a…`, stage `draft`,
`reviews: []`, `revisao_factual_humana_pendente: true`.

## O que o artigo afirma (4 pontos)

| # | Afirmação | Fonte declarada | O que eu pude verificar | Situação |
|---|-----------|-----------------|--------------------------|----------|
| 1 | Em 14/11, Reuters atribuiu à Binance cobertura de 95% e retiradas reabrindo progressivamente | Reuters | Reuters **bloqueia leitura automática** (HTTP 401, inclusive via proxy de leitura). Não verificado | **Pendente** |
| 2 | Em 31/10, a empresa disse ter reposto 90% e buscar tokens de menor liquidez | Fidelity/Reuters | Tecnoblog (14/11) confirma que "os últimos 10%" vieram de compra de tokens (bolsa e OTC), compatível com 90% em 31/10. A expressão **"menor liquidez" não aparece** em fonte acessível | **Pendente (paráfrase)** |
| 3 | Mais de US$ 2,7 bi congelados, mais de US$ 1,2 bi sob autorização judicial americana | AP News | **Confirmado no corpo da AP**: "the U.S. government and private sector have so far combined to freeze more than $2.7 billion… the Justice Department… obtained court authorization to seize or restrain more than $1.2 billion of that total" | **Confirmado** |
| 4 | Tecnoblog: Binance cobriu 100% dos ativos e publicou prova de reservas | Tecnoblog | **Confirmado literalmente**: "cobriu 100% dos US$ 6,3 bilhões… também foi publicada uma nova Prova de Reserva" | **Confirmado** |

## O que falta de você (virou 1 decisão, não 4)

Os dois pendentes vêm da **mesma fonte bloqueada (Reuters)**. Então:

**Abrir a Reuters uma vez** (link abaixo) e confirmar dois pontos:
- 95% de cobertura, em 14/11
- "tokens de menor liquidez", em 31/10

https://www.reuters.com/legal/government/binance-targets-full-reopening-withdrawals-by-next-week-2026-11-14/

- Se confirmar os dois → os 4 claims ficam verificados e a revisão pode ser registrada.
- Se a página não abrir, a alternativa é **suavizar o texto** (retirar "95%" e
  "menor liquidez"). Isso exige nova versão do artigo e **invalida o hash atual**
  `a80b3e39…` — a revisão recomeça.

Recomendação: tentar a Reuters primeiro; é o caminho que não mexe no texto.

## Como registrar depois (para o Gate aceitar)

- Revisão precisa de **trecho literal** vinculado ao texto; o campo `evidence` do
  pacote é uma cópia da própria afirmação, não uma prova — por isso o Gate exige
  revisão humana separada.
- Se o próprio proprietário revisar, o modo é `review_mode=owner` (não é revisão
  independente por terceiro).
- Sem `reviews[]` preenchido, o Gate continua bloqueando — corretamente.

## Achado de transparência

`rastreabilidade_claims` marca os 4 itens como `texto_localizado: false`, ou seja,
a frase da afirmação não aparece literalmente no corpo do artigo. Isso não é
erro: o texto parafraseia. Mas significa que a conferência é **semântica**, feita
por pessoa, não automática.

## Situação após a conferência pública (17/11)

- 2 de 4 afirmações confirmadas com trecho literal de fonte acessível.
- 2 de 4 dependem de uma única fonte bloqueada (Reuters).
- Nenhuma afirmação foi considerada falsa; nenhuma foi aprovada.
- Acesso automático à Reuters é inviabilizado por proteção anti-robô — a
  verificação final é necessariamente humana.
