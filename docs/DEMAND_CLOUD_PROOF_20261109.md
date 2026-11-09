# Demanda real BR — prova limitada, 09/11/2026

## Escopo

Reutiliza `research_signals.trends`, sem IA, API paga, credenciais, WordPress,
alteração de fila ou cron. Um pedido manual do proprietário por Issue exata
`[demand-probe] validar Trends BR 7 dias` executa no repo público original,
runner Ubuntu padrão, limite de três minutos, sem artifacts/cache.

O job lê uma vez o feed existente e usa até três títulos exatos como consultas
explícitas em uma comparação Trends BR/now 7-d. Isso verifica disponibilidade
e sinal dessas strings: não extrai produtos nem prova demanda de uma pauta
reformulada ou de um produto. Títulos não são truncados silenciosamente.

## Adaptador e limites

Pacote opcional auditado: trendspyg 1.9.0, MIT, fonte flack0x/trendspyg, wheel
PyPI consultado em 09/11. HTTP somente; sem engine auto/browser, cookies em disco,
archive/cache ou serviços novos. Selenium é dependência declarada do pacote,
mas nenhum navegador/driver é iniciado ou baixado pelo fluxo HTTP. Uma comparação
é composta por handshake e chamadas de widgets, não por um único GET.

Desativa geo/related e configura max_retries=1. O engine HTTP do pacote interrompe
em recusa 403/429 sem fallback. A prova inteira tem limite no Actions. Não
reexecutar em loop para contornar indisponibilidade. O adapter ausente/recusado
continua estado explícito; nunca demanda zero.

## Normalização offline e alternativa sem provedor

`demand_normalization.normalize_trends(raw, term, now=...)` aceita envelope
Explore/comparison preservando consulta, geo, timestamp, URL e grupo compartilhado.
Janela de sete dias termina na última hora UTC fechada do fetched_at. Pontos
parciais/fora dela são excluídos e contados; não são preenchidos. Contrato existente
valida cobertura diária, ordem, duplicatas, valores 0..100 e atualidade. Um sinal
observado não certifica relevância da consulta, factualidade ou publicação.

O JSON normalizado temporário é reaproveitável no contrato/importador existente.
Exportação manual revisada CSV/JSON continua alternativa gratuita e independente
do trendspyg; não depende de uma ferramenta de IA. Dados ausentes não autorizam
seleção. Snapshot fica temporário no executor; só resumo seguro sai no log.

## Validação

49 testes direcionados passaram; 29 com python -S. Cobrem associação ao termo,
região incorreta, período parcial, valores inválidos, duplicatas, futuro, contexto
compartilhado, fila e controles do workflow. Fixtures não comprovam Trends real.
O resultado externo deve ser registrado na Issue de execução, mesmo se bloqueado.

Staging do site está desativado conforme informação do usuário. Este fluxo não
reativa staging nem depende dele e não modifica o site em produção.
