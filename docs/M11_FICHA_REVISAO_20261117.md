# M11 — Ficha de revisão do artigo Binance — 17/11/2026

Preparado para reduzir a revisão humana ao mínimo necessário. **Nada foi
publicado, aprovado ou alterado.** Pacote `a80b3e398683cb6a…`, stage `draft`,
`reviews: []`, `revisao_factual_humana_pendente: true`.

## O que o artigo afirma (4 pontos)

| # | Afirmação | Fonte declarada | O que eu pude verificar | Situação |
|---|-----------|-----------------|--------------------------|----------|
| 1 | Em 14/11, Reuters atribuiu à Binance cobertura de 95% e retiradas reabrindo progressivamente | Reuters | Reuters **bloqueia leitura automática** (HTTP 401). Não verificado | **Pendente** |
| 2 | Em 31/10, a empresa disse ter reposto 90% e buscar tokens de menor liquidez | Fidelity/Reuters | Tecnoblog (14/11) diz que "os últimos 10%" foram obtidos por compra de tokens — compatível com 90% em 31/10. A expressão "menor liquidez" **não** aparece | **Parcial** |
| 3 | Mais de US$ 2,7 bi congelados, mais de US$ 1,2 bi sob autorização judicial americana | AP News | AP: manchete **"US seizes $1.2 billion in cryptocurrency stolen from Binance"** — confirma o valor de 1,2 bi sob apreensão. Os 2,7 bi não foram conferidos | **Parcial** |
| 4 | Tecnoblog: Binance cobriu 100% dos ativos e publicou prova de reservas | Tecnoblog | **Confirmado literalmente**: "cobriu 100% dos US$ 6,3 bilhões… também foi publicada uma nova Prova de Reserva" | **Confirmado** |

## O que falta de você (4 decisões)

1. **Claim 1** — abrir a Reuters e confirmar os 95% e a data 14/11. Se não abrir,
   decidir: retirar o número ou manter citando apenas o que está comprovado.
2. **Claim 2** — confirmar se "tokens de menor liquidez" existe na fonte. Se não,
   trocar por "compra de tokens".
3. **Claim 3** — conferir o valor de US$ 2,7 bi congelados. Se não confirmar,
   manter só o 1,2 bi (esse está comprovado).
4. **Claim 4** — nenhuma ação: está confirmado.

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
