# Desenvolvimento e avaliação substantiva editorial

Base auditada: MKT-RSS `5741f4914fa00cc7e0e10a9755ab486f52538044`.
Branch: `fix/editorial-substance-20261110`.

## Causas comprovadas

1. A importação preservava texto pronto, sem adaptação editorial. O prompt do
   gerador priorizava reescrita/tradução integral, sem recorte específico de pauta.
2. A prontidão aceitava prova de prompt e medidas estruturais como requisito
   editorial. Um teste preenchia o corpo com frases repetidas e esperava que fosse
   considerado pronto ao receber fontes, imagem e links. Foi corrigido para
   reprovar esse caso; metadados completos continuam insuficientes.
3. O workflow manual de homologação executava `897c38e...`, anterior às correções
   de voz. A integração na master não atualizava aquele runtime.
4. O prompt cortava silenciosamente o insumo após 9.000 caracteres, podendo
   eliminar contexto e ressalvas. A saída não rejeitava truncamento por tokens.
5. A prontidão exigia exatamente três links, contrariando o DNA que permite até
   três relações reais; o importador também não encaminhava evidências de mídia
   e links para essa checagem.

## Comportamento implementado

- Briefing com gênero, leitor, necessidade, recorte, contribuição e limites.
  RSS usa o briefing fornecido ou solicita planejamento ao provedor existente.
- Online, importados pendentes passam automaticamente por adaptação e crítica;
  `--adapt-editorial` somente força nova adaptação de versão já avaliada.
  `--offline` nunca chama provedor e expõe desenvolvimento não executado.
- RSS e adaptação de importados permitem até duas redações/críticas. A crítica
  retorna como feedback separado, sem mudar o briefing nem cortar justificativas
  para encaixá-las no campo contribution. Não há retries invisíveis do SDK.
- A crítica do RSS avalia o texto final, com atribuição e links. A rota especializada
  CT-006 também chama planejamento e crítica; resultado insuficiente fica pendente.
- Avaliação substantiva exige cinco critérios (necessidade, recorte, apoio à
  decisão, voz, limites), justificativas específicas e trechos literais do artigo.
  Texto e briefing são vinculados por hashes. Cada critério exige ao menos 3/4
  para triagem; não é a antiga nota geral 85/100 nem certificação de qualidade.
  Repetição continua pendente mesmo quando alguém fornece notas altas.
- Alterar o texto invalida a avaliação e atestados de adaptação anteriores.
  Vincular nova avaliação nunca repara um pacote previamente inválido.
- ASSISTED_ADAPTED identifica adaptação real por Codex/ChatGPT vinculada ao conteúdo,
  sem fingir aceite humano nem chamada a system prompt externo que não ocorreu.
- O importador encaminha mídia/direitos e links verificados fornecidos pelo
  chamador. O chamador continua responsável por evidência real; a função não
  autentica uma declaração de direitos. Zero a três links relacionados são aceitos;
  links presentes sem verificação e mais de três links continuam pendentes.
- O workflow manual usa github.sha: snapshot imutável da própria execução,
  evitando continuar no build antigo após integrar correções. Não ativa cron.
- O insumo é preservado até 60.000 caracteres; acima disso a operação exige
  dividir a apuração. Resposta com finish_reason=length é rejeitada.
- Manifestos distinguem execução de resultado. Falha, falta de avaliação ou
  esgotamento do limite não viram PASS, aceite humano ou autorização de publicação.

## Caso real e limites da evidência

Foi recuperado o rascunho WordPress #9798 e relidas as quatro páginas oficiais
citadas. A versão recuperada tem 933 palavras pela contagem do módulo, diferente
da versão de 1.213 palavras relatada na conversa anexada. A auditoria usa a versão
real lida nesta sessão; não trata o relato antigo como prova do estado atual.

Foi preparada adaptação de 927 palavras com os mesmos insumos. O recorte ordena o
diagnóstico pelo alcance da intervenção e explica dependências/custos. Original e
adaptação passaram pelos módulos reais offline. A avaliação substantiva foi feita
pela mesma sessão Codex que escreveu a adaptação: é assistida, não independente,
cega ou aceite do proprietário. As notas não comprovam qualidade de todos os
artigos nem padrão acima da média.

O rascunho #9798 foi atualizado com título, slug e corpo reprocessado. O readback
confirmou status draft, autor 3, imagem 9799 e igualdade exata do HTML de blocos.
Nenhum artigo foi publicado. Texto privado, fontes capturadas, avaliações com
citações e backup ficam fora do repositório público; só recibo redigido é versionado.

Não houve chamada real ao Groq nesta sessão: o ambiente não possui a credencial;
o gh do terminal também não tem autenticação válida para despacho de Actions.
O conector GitHub está disponível para código/PR/CI. Não foi copiado segredo nem
confirmada quota gratuita por inferência. Os testes com doubles comprovam fluxo,
não desempenho do modelo. O adaptador factual legado segue restrito a notícia;
não ampliamos o contrato a guia apenas trocando rótulos. Factualidade, direitos de
mídia e aceite humano continuam revisões separadas.

## Referências de execução

- `mkt_flow_p0/editorial_development.py`: planejamento, crítica, adaptação limitada.
- `mkt_flow_p0/editorial_substance.py`: briefing, rubrica e vínculo ao texto.
- `pipeline_rss.py`: integração RSS e CLI de importação online/offline.
- `tools/produce_bank_article.py`: integração na rota especializada CT-006.
- `tests/test_editorial_substance.py`: regressões, falhas, finalização e limites.
- `tasks/EDITORIAL-SUBSTANCE-20261110.json`: checkpoint e evidências.

Nova recomendação: usar uma avaliação cega do proprietário de artigos com os
mesmos insumos para calibrar a crítica assistida, sem premiar extensão ou bordões.
