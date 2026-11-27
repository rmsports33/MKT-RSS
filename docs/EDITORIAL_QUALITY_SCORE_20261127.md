# Avaliador editorial 0–100 do MKT-RSS (27/11/2026)

## O que é

`mkt_flow_p0/editorial_quality_score.py` lê o contrato único copiado em
`data/editorial-quality-v1.json` (hash `e9158844…`) e produz um **recibo de qualidade**
para cada artigo. Não é aprovação, não prova fatos e não publica.

## Como a nota é formada

| Parte | Peso | Origem |
|---|---:|---|
| Nota assistida | 70% | Rubrica 0–4 dos 5 critérios × 5 |
| Nota estrutural | 30% | Checagens determinísticas + cobertura do mapa Canaltech |

Bloqueios (fonte única, direito de imagem, links acima de 3, voz ausente,
contexto brasileiro inventado) limitam a nota a **69**. Avisos (sem links
internos, vídeo fora de review, texto curto) descontam 5 pontos cada.

## Padrão de comparação

O mapa de raciocínio vem da análise Canaltech do Galaxy S26 FE salva no projeto.
São comparados os movimentos — problema do leitor, tese, evidências,
consequências, trade-offs e veredito condicional — nunca o texto ou o template.

## Público brasileiro

Relevância local entra apenas com fonte. Menções negativas ("não há dados
brasileiros") não são penalizadas. Contexto afirmativo sem fonte bloqueia.
Sem fonte brasileira, a regra é pesquisar notícia semelhante em sites tech/afins
e registrar como `PENDING_HUMAN_REVIEW`.

## Integração

- `editorial_import.processar_artigo_importado` grava `quality-receipt.json` no pacote;
- `resumo_execucao` inclui `quality_score`;
- Gate V1 mostra a nota assistida e exige a nota humana (0–100).

## Exemplo real — #9925

Nota assistida 100, estrutural 63, **nota final 69**. Bloqueio: `multifonte`
(uma fonte apenas). Pendência: `pesquisa_fallback`. Cobertura do mapa Canaltech: 0,67.
Isso representa honestamente o artigo: bem avaliado pela rubrica assistida, mas
ainda abaixo do padrão por falta de apuração multifonte.

## Padrão vivo (opção 2)

`mkt_flow_p0/editorial_golden_set.py` guarda, por gênero, até 3 artigos com
**nota humana alta, aprovação explícita e fatos conferidos**. O prompt recebe só
descritores de forma — tipo de abertura, funções das seções, movimentos
Canaltech e padrão de veredito. Nunca entra frase ou parágrafo do artigo usado
como referência.

Regras:

- nota assistida sozinha **não** registra padrão;
- limite provisório: 70/100, até você confirmar a linha de corte;
- registro por `tools/atualizar_golden_set.py`, após a nota no Gate;
- se o contrato mudar, o padrão antigo é recusado por hash desatualizado.

O conjunto começa **vazio**: nenhum artigo foi promovido sem sua nota humana.

## Testes

`tests/test_editorial_quality_score.py` (7) e `tests/test_editorial_golden_set.py` (5).
Suíte relacionada executada: 107 testes aprovados, sem rede.


## Contrato 1.1 e ASVE

Contrato canônico sincronizado: SHA-256 `e915884437f1ddad629b59a575d312fcb2f36e18cb1c2b855880e4931c867512`.
O contrato agora registra:
- lema editorial oficial e princípio de conhecimento conectado;
- pesquisa global antes do recorte brasileiro para temas de alcance mundial;
- papéis e estados de evidência por afirmação, sem confiança automática em domínio/TLD;
- estrutura H1/H2/H3 específica e narrativa, sem metacomentários;
- links internos contextuais, sem quota mínima;
- ASVE com contexto independente, limite de 0–5 achados, P0/P1/P2, sem reescrita e sem autorização de publicação.

Implementação associada:
- `data/editorial-primary-source-registry-v1.json` e `mkt_flow_p0/primary_source_registry.py`;
- `mkt_flow_p0/editorial_secondary_analysis.py`;
- testes em `tests/test_primary_source_registry.py` e `tests/test_editorial_secondary_analysis.py`.

O hash do contrato identifica a versão de regras; não demonstra que o artigo foi pesquisado, que uma fonte é verdadeira ou que a revisão foi executada. A ASVE usa um analisador injetado no orquestrador atual, sem segundo serviço/modelo automático e sem novo custo por padrão.
