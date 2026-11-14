# Brief de correção factual — Binance, 14/11/2026

**Estado:** revisão obrigatória; NÃO aprovado para WordPress/publicação. Este documento é instrução de apuração, não alteração do pacote versionado da Hostinger.

## Problema editorial identificado
O artigo gerado traz o título categórico "Binance cobre US$ 6,3 bi de roubo", resumo com cobertura de 100%, e somente uma fonte, sem mapa de evidências. Há divergência entre declarações publicadas sobre a extensão da cobertura; não tratar como equivalentes os conceitos de **fundos separados para cobertura**, **tokens repostos em carteiras**, **ativos congelados** e **valores efetivamente recuperados**. Data do ataque: **29/10/2026**, não 2023.

## Propostas para a revisão do texto real
- Título mais fiel: **Binance afirma cobrir prejuízo de US$ 6,3 bilhões após ataque; entenda o que ainda falta comprovar**.
- Abertura: **A Binance afirmou em 12 de novembro que havia concluído a cobertura das perdas causadas pelo ataque de 29 de outubro de 2026. Uma reportagem da Reuters de 14 de novembro, porém, cita cobertura de 95% e informa que parte das retiradas ainda estava sendo restabelecida. Os indicadores podem se referir a escopos, momentos ou critérios diferentes, que precisam ser esclarecidos antes de apresentar a reposição como fato independente.**
- Diferenciar ressarcimento de saldos de recuperação do dinheiro roubado; descrever SAFU/seguro de futuros/tesouraria somente com atribuição; não inferir aprovação externa a partir de um snapshot de reservas.
- Atribuição sobre TraderTraitor: investigadores e autoridades vinculam o ataque ao grupo; distinguir atribuição de alegação provada em juízo.
- Ângulo brasileiro: impactos práticos de atrasos nas retiradas, concentração de custódia e checagem de comunicado/PoR; não sugerir proteção garantida nem aconselhamento individual de investimento.
- Não publicar cifra de R$ 34 bilhões como conversão atual sem data e fonte do câmbio; referir que Tecnoblog usou aproximação em 14/11.

## Fontes verificáveis para cruzamento
1. Tecnoblog, 14/11/2026, reproduz afirmação de **100%** feita pela Binance em comunicado de 12/11: https://tecnoblog.net/noticias/r-34-bilhoes-binance-cobriu-100-do-prejuizo-do-maior-roubo-de-cripto-da-historia/
2. Reuters, 14/11/2026, cita **95%** e reabertura de retiradas em fases: https://www.reuters.com/legal/government/binance-targets-full-reopening-withdrawals-by-next-week-2026-11-14/
3. Reuters, 31/10/2026, sobre reposição de cerca de US$ 6 bi e recursos próprios: https://www.reuters.com/legal/government/binance-says-90-stolen-assets-replenished-2026-10-31/
4. AP, 13/11/2026, sobre ativos apreendidos/congelados: https://apnews.com/article/41be4834083e596a8facfd719f851cae
5. CoinDesk, 30/10/2026, sobre US$ 6,34 bi **reservados**, compra de tokens e apuração inicial do ataque: https://www.coindesk.com/business/2026/10/30/binance-arranges-usd6-34-billion-to-cover-losses-from-record-crypto-hack

**Pendência:** validar as fontes primárias (comunicado Binance e PoR, atribuição FBI/TRM), comparar os horários e reescrever o texto completo usando somente alegações sustentadas. Antes da aprovação humana, anexar mapa real de claims, revisão substantiva e direitos/legenda/alt da imagem. A imagem original do Tecnoblog não está automaticamente liberada para reutilização.

## Próximo passo sem geração nova nem custo de tokens
```bash
cd ~/mkt-rss-runner
git pull --ff-only origin feat/hostinger-runtime-independente-20261113
bash ops/hostinger/conexo_editorial.sh --show-article
```
Esse comando apenas imprime o Markdown local para correção; não reescreve, aprova ou publica.
