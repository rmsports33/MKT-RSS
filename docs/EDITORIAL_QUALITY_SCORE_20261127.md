# Avaliador editorial 0–100 do MKT-RSS (27/11/2026)

## O que é

`mkt_flow_p0/editorial_quality_score.py` lê o contrato único copiado em
`data/editorial-quality-v1.json` (hash `e9158844…`) e produz um **recibo diagnóstico**
para cada artigo. Não é aprovação factual, não substitui a decisão editorial e
não publica. Nota alta nunca autoriza publicação.

## Como a nota é formada

| Parte | Peso | Origem |
|---|---:|---|
| Nota assistida | 70% | Rubrica 0–4 dos cinco critérios × 5 |
| Nota estrutural | 30% | Checagens determinísticas e, quando aplicável, mapa de raciocínio |

Bloqueios estruturais atuais (por exemplo, multifonte insuficiente, direitos de
imagem não confirmados ou voz editorial sem proveniência) limitam a nota a 69.
Os avisos reduzem a nota, mas não bloqueiam aprovação por si só. Todos os
resultados permanecem sujeitos à revisão humana e às verificações independentes.

## Links internos: pertinência, não quota

O contrato não estabelece número mínimo de links internos. A ausência de link
não reduz a nota. Mais de três links gera apenas um aviso suave para o editor
examinar se todos são úteis, contextuais e realmente publicados. O aviso não é
bloqueio e não implica que quatro links sejam automaticamente excessivos.

O avaliador não deve inventar destino nem considerar uma URL no texto como prova
de que a página é pertinente. A ASVE recebe somente páginas reais publicadas
no catálogo fornecido pelo executor.

## Mapa de raciocínio Canaltech

A referência vem da análise Canaltech do Galaxy S26 FE salva no projeto. Ela é
um **mapa de raciocínio**, não um template universal. A heurística só se aplica
a gêneros comparativo e review, nos quais avaliação condicional, perfis de
leitor e trade-offs têm pertinência direta. Notícias, análises, guias e notas
breves não recebem penalidade por não reproduzir essa estrutura.

Perguntas nos títulos não são requisito. A verificação de preço/data só é
considerada quando o próprio artigo aborda preço ou disponibilidade.

## Contexto brasileiro: sinalização, não aprovação automática

A detecção lexical de contexto brasileiro não comprova suporte documental. Um
domínio `.gov.br` ou `.com.br`, a menção a “Brasil” ou a presença de uma fonte
local não demonstram que aquela fonte sustenta uma afirmação específica.

Quando o texto contém afirmações brasileiras, o recibo sinaliza
`REVIEW_REQUIRED` em caráter consultivo, sem bloquear nem reduzir a nota. A
validação deve ocorrer por claim, com fonte, localização exata, escopo,
metodologia e limitações no dossiê de evidências, além da revisão humana.
A ausência de dados brasileiros pode ser um limite legítimo e deve ser
explicitada, não tratada como falha automática.

## Integração

- `editorial_import.processar_artigo_importado` grava `quality-receipt.json` no pacote;
- `resumo_execucao` inclui `quality_score`;
- Gate V1 exibe a nota assistida e exige a avaliação humana separada;
- o recibo de qualidade não é autorização de publicação nem substitui o Gate.

## Exemplo histórico — artigo #9925

A avaliação anterior do #9925 registrou nota final limitada a 69 por insuficiência
multifonte. A decomposição estrutural daquela execução incluiu a antiga heurística
Canaltech aplicada a gênero não compatível e, portanto, **não deve ser usada como
referência para a regra atual**. Não foi executada nova avaliação do post nesta
alteração; qualquer nota atual exige uma nova execução com o mesmo conteúdo,
dossiê completo e contrato sincronizado.

## Padrão vivo (opção 2)

`mkt_flow_p0/editorial_golden_set.py` guarda, por gênero, até três artigos com
**nota humana alta, aprovação explícita e fatos conferidos**. O prompt recebe só
descritores de forma — tipo de abertura, funções das seções, movimentos
compatíveis com o gênero e padrão de conclusão. Nunca entra frase ou parágrafo
do artigo usado como referência.

Regras:

- nota assistida sozinha **não** registra padrão;
- limite provisório: 70/100, ainda não confirmado como corte editorial;
- registro por `tools/atualizar_golden_set.py`, após a nota humana no Gate;
- se o contrato mudar, o padrão antigo é recusado por hash desatualizado.

O conjunto começa **vazio**: nenhum artigo foi promovido sem sua nota humana.

## Testes e estado de validação

- `tests/test_editorial_quality_score.py`: 10 casos (inclui regressões para links sem quota bloqueante, aplicação por gênero e ausência de PASS baseada somente em domínio).
- `tests/test_editorial_golden_set.py`: 5 casos.
- A suíte anterior relacionada registrou 107 testes aprovados antes das alterações desta branch.
- Os três novos testes de regressão e as mudanças de scoring desta revisão **ainda não foram executados** em ambiente de desenvolvimento. Não declarar PASS com base apenas em inspeção estática.

## Contrato 1.1 e ASVE

Contrato canônico sincronizado: SHA-256
`6b55c87c15b004169a77a73d3064fb02072c1cc370e7c9be68bee20e9abde9f7`.

O contrato registra:
- lema editorial oficial e princípio de conhecimento conectado;
- pesquisa global antes do recorte brasileiro para temas de alcance mundial;
- papéis e estados de evidência por afirmação, sem confiança automática em domínio/TLD;
- estrutura H1/H2/H3 específica e narrativa, sem metacomentários;
- links internos contextuais, sem quota mínima;
- ASVE com contexto independente, limite de 0–5 achados, P0/P1/P2, sem reescrita e sem autorização de publicação.

Implementação associada:
- `data/editorial-primary-source-registry-v1.json` e `mkt_flow_p0/primary_source_registry.py`;
- `mkt_flow_p0/editorial_secondary_analysis.py`;
- testes em `tests/test_primary_source_registry.py` e
  `tests/test_editorial_secondary_analysis.py`.

O hash do contrato identifica a versão de regras; não demonstra que o artigo foi
pesquisado, que uma fonte é verdadeira ou que a revisão foi executada. A ASVE
usa o analisador injetado no orquestrador atual, sem segundo serviço/modelo
automático e sem novo custo por padrão.
