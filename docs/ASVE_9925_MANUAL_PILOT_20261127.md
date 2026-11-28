# Piloto manual de ASVE — artigo WordPress #9925

**Status:** análise secundária editorial manual, somente leitura.  
**Não é:** recibo produzido pelo módulo ASVE, aprovação editorial, autorização de publicação ou alteração do artigo.  
**Contrato:** ConexoTech v1.1 — SHA-256 `6b55c87c15b004169a77a73d3064fb02072c1cc370e7c9be68bee20e9abde9f7`.

## Identificação da versão analisada

- Post: `9925`
- Título atual: `Paradoxo de Jevons: IA mais eficiente pode elevar consumo`
- Estado WordPress: `draft`
- Última modificação observada: `2026-11-27T08:01:53`
- Hash SHA-256 do conteúdo HTML bruto lido em contexto `edit`:  
  `7cdd3e4e3b6abd6d18ced7769c8491f151b517e3ee9539b8ef1f583840354ece`
- Comprimento do HTML bruto: 6.490 caracteres.
- O hash identifica exatamente a versão lida. Qualquer mudança no conteúdo exige nova leitura e nova análise.

## Resultado

**Quatro apontamentos P1 e dois P2.** Os P1 são melhorias materiais a considerar antes da publicação. Os P2 são pautas autônomas e não devem ser incorporadas integralmente ao artigo atual.

Esta leitura não reescreve o texto e não substitui a revisão principal, a ASVE automatizada ou a decisão humana no Gate.

---

## P1 — Melhorias materiais para o artigo atual

### P1-01 — O artigo começa no Brasil, mas o problema é mundial

**Localização:** abertura e primeira seção.

**Apontamento:** o texto apresenta a expansão dos data centers no Brasil sem situar o leitor na escala internacional da disputa por eletricidade. Isso deixa de fora a dimensão que explica por que o problema está se tornando estratégico: consumo mundial dos data centers, concentração regional, ritmo de crescimento e diferenças entre sistemas elétricos.

**Por que importa:** sem o panorama mundial, a expansão brasileira parece um evento isolado. O leitor perde a comparação entre regiões com grande concentração de data centers e regiões que enfrentam outros desafios de acesso, geração e infraestrutura.

**Evidência para incorporar:**
- A IEA estima que o consumo elétrico mundial dos data centers passe de aproximadamente 485 TWh em 2025 para 950 TWh em 2030; é projeção, não medição futura garantida.
- Os dados da IEA mostram forte concentração em América do Norte e Ásia-Pacífico, com escalas muito diferentes das observadas na América Central e do Sul e na África.
- A Ember informa que a energia solar respondeu por 75% do crescimento líquido da demanda mundial de eletricidade em 2025 e que as renováveis atingiram 33,8% da geração global, acima do carvão, com 33%.

**Ação recomendada:** inserir um contexto global curto antes do recorte brasileiro, selecionando diferenças regionais que alterem a interpretação. Não criar uma lista enciclopédica de países nem alongar a matéria com detalhes sem ligação direta à tese.

**Fontes de origem:**
- IEA — *Key Questions on Energy and AI*, atualização 2026: https://www.iea.org/reports/key-questions-on-energy-and-ai/executive-summary
- IEA — *Energy and AI*: https://www.iea.org/reports/energy-and-ai/executive-summary
- Ember — *Global Electricity Review 2026*: https://ember-energy.org/pt-br/analise/global-electricity-review-2026/

### P1-02 — Substituir a reportagem secundária pelo documento original da EPE e explorar o que ele realmente acrescenta

**Localização:** seção que apresenta a projeção brasileira de 3 TWh para 30 TWh.

**Apontamento:** a reportagem da MegaWhat é útil como cobertura jornalística, mas o artigo já pode citar diretamente o PDE 2036 da EPE. O documento original contém detalhes que a reportagem resumida não substitui e que dão uma contribuição editorial adicional.

**Por que importa:** a EPE não projeta apenas crescimento do consumo. Ela também descreve ganhos de eficiência em hardware, software e refrigeração enquanto estima a expansão dos data centers. Essa coexistência é diretamente relevante para a discussão entre eficiência por operação e consumo agregado.

**Evidência localizada nas fontes originais:**
- Relatório Síntese PDE 2036, versão 1 para Consulta Pública, de outubro de 2026: a tabela/gráfico da página impressa 60 apresenta 3 TWh para data centers em 2026 e 30 TWh em 2036. A EPE afirma que os grandes empreendimentos tendem a buscar conexão direta à rede básica.
- Caderno de Demanda de Energia PDE 2036, versão 1 publicada em 27/10/2026: a página impressa 36 repete 3 TWh em 2026 e 30 TWh em 2036 e informa que a projeção foi fundamentada no Planejamento da Operação Energética (PLAN) 2026–2030, considerando a evolução dos pedidos de acesso à rede básica.
- **Ressalva estatística material:** o Relatório Síntese, p. 58 e p. 67, e o Caderno de Demanda, p. 22, também apresentam taxa média de crescimento anual de 13,7% para a demanda de data centers até 2036. Essa taxa não reconcilia aritmeticamente com a série de 3 para 30 TWh se ambas forem interpretadas como a mesma grandeza, base e período: 3 → 30 TWh em dez anos equivale a CAGR aproximado de 25,9%. As fontes consultadas não explicam explicitamente essa diferença. Não publicar as duas métricas como se fossem a mesma série até obter esclarecimento da EPE sobre escopo, base, período ou eventual revisão.
- Caderno de Demanda, p. 36: a projeção de data centers corresponde a aproximadamente 3.400 MW médios no SIN em 2036, cerca de 3% da carga naquele ano. A nota explica que MW médio é uma carga média horária e permite conversão para TWh.
- Relatório Síntese, p. 67–68: a EPE espera ganhos de eficiência em hardware, software, virtualização, compressão de modelos, gerenciamento de potência e refrigeração, inclusive refrigeração indireta a líquido. O próprio relatório ressalta que clima quente e úmido limita o aproveitamento do ar/água externos e eleva a dependência de refrigeração mecânica.
- PUE mede o consumo total da instalação dividido pelo consumo dos equipamentos de TI. Portanto, mede a eficiência do uso de energia da instalação e dos sistemas auxiliares, não a eficiência computacional dos próprios servidores. O documento recomenda indicadores complementares que relacionem processamento e consumo dos equipamentos de TI.
- O Relatório Síntese consultado é explicitamente V1 para Consulta Pública, divulgada em 07/10/2026. O MME informa que a consulta pública do PDE 2036 ocorreu de 08/10 a 06/11/2026; portanto, esse relatório não deve ser descrito como versão final aprovada. O Caderno de Demanda é V1, com publicação inicial em 27/10/2026.

**Ação recomendada:** usar os documentos originais da EPE como fontes primárias, indicar que são projeções da versão consultada do PDE 2036 e explicar o método/escopo quando disponível. Antes da publicação, pedir esclarecimento à EPE sobre a taxa de 13,7% versus a série 3→30 TWh. Incorporar a distinção entre eficiência de TI e PUE: é uma das contribuições mais relevantes para ligar a discussão de eficiência dos modelos à energia consumida pela instalação inteira.

**Fontes de origem:**
- EPE/MME — *Plano Decenal de Expansão de Energia 2036, Relatório Síntese*, V1 para Consulta Pública, outubro de 2026: https://epe.gov.br/sites-pt/publicacoes-dados-abertos/publicacoes/PublicacoesArquivos/publicacao-982/topico-860/PDE%202036_Relat%C3%B3rio%20S%C3%ADntese_rev3_2026-10-08.pdf
- EPE — *PDE 2036, Caderno de Demanda de Energia*, V1 publicada em 27/10/2026: https://www.epe.gov.br/sites-pt/publicacoes-dados-abertos/publicacoes/PublicacoesArquivos/publicacao-982/topico-851/PDE%202036_Caderno%20de%20Demanda%20de%20Energia_v1_2026-10-27.pdf
- MME — abertura da consulta pública do PDE 2036 e prazo de contribuições até 06/11/2026: https://www.gov.br/mme/pt-br/assuntos/noticias/julho-26/mme-abre-consulta-publica-do-plano-decenal-de-expansao-de-energia-2036/

### P1-03 — Separar capacidade contratada, potência e energia efetivamente consumida

**Localização:** parágrafo sobre 1 GW em 2026, 1,5 GW em 2027 e equivalência com uma cidade de um milhão de habitantes.

**Apontamento:** o texto deve distinguir capacidade elétrica contratada, potência (GW) e energia consumida ao longo do tempo (TWh). A equivalência com o consumo de uma cidade deve ser atribuída ao Ministério como comparação ilustrativa, não apresentada como medição real do consumo contínuo dos data centers.

**Por que importa:** capacidade contratada não comprova que toda a potência será utilizada continuamente. Misturar GW com TWh pode levar o leitor a concluir que os data centers já consomem efetivamente uma quantidade de energia que o comunicado não mediu.

**Ação recomendada:** atribuir os números ao MCom/Associação Brasileira de Data Center, explicar que são dados de capacidade contratada e previsão, e deixar explícito que não equivalem a consumo anual efetivamente medido. Manter separada a projeção de consumo em TWh da EPE.

**Fonte de origem:**
- Ministério das Comunicações — comunicado de 25/11/2026: https://www.gov.br/mcom/pt-br/noticias/2026/novembro/com-avanco-da-ia-capacidade-energetica-para-data-centers-no-brasil-deve-crescer-50-em-2027

### P1-04 — Explicar Jevons com rigor e remover a dependência da Wikipedia

**Localização:** seção sobre o paradoxo de Jevons e referências bibliográficas.

**Apontamento:** a referência à Wikipedia deve ser substituída pela obra original de Jevons e por literatura científica. O texto deve diferenciar efeito rebote de *backfire* e não sugerir que o paradoxo prova que os ganhos de eficiência da IA necessariamente resultarão em aumento líquido do consumo.

**Por que importa:** o crescimento dos data centers e a eficiência dos chips são fatos/projeções observáveis; que os ganhos de eficiência estejam causando o aumento agregado é uma afirmação causal diferente. A literatura não sustenta uma conclusão universal de *backfire*.

**Ação recomendada:**
- Usar *The Coal Question* (primeira publicação em 1865) como fonte histórica do conceito.
- Diferenciar o efeito rebote, que reduz parte da economia prevista, de *backfire*, quando o aumento de consumo supera a economia inicial.
- Citar a revisão de Sorrell et al. (2009) e Gillingham, Rapson e Wagner (2016), contextualizando setor e limites da evidência.
- Tratar o caso dos data centers como uma questão atual a investigar, não como comprovação empírica de um efeito rebote brasileiro já medido.

**Fontes:**
- Jevons — *The Coal Question*: https://www.econlib.org/library/YPDBooks/Jevons/jvnCQ.html
- Sorrell, Dimitropoulos e Sommerville (2009) — *Empirical estimates of the direct rebound effect: A review*: https://doi.org/10.1016/j.enpol.2008.11.026
- Gillingham, Rapson e Wagner (2016) — *The Rebound Effect and Energy Efficiency Policy*: https://doi.org/10.1093/reep/rev017

---

## P2 — Pautas futuras, sem ampliar artificialmente o artigo atual

### P2-01 — Data centers, redes elétricas e confiabilidade: onde a nova demanda pode encontrar limites

**Oportunidade:** aprofundar os requisitos de conexão, transmissão, carga contínua, disponibilidade, concentração geográfica e planejamento do sistema elétrico.

**Valor editorial:** o Caderno de Demanda da EPE informa que a projeção de data centers corresponde a cerca de 3.400 MW médios no SIN em 2036 e que os projetos dependem de pedidos de acesso à rede básica. O Relatório Síntese indica que mais de 65% dos novos investimentos de grande porte são esperados no Sudeste/Centro-Oeste, quase 30% no Nordeste e cerca de 5% no Sul. Essa concentração permite investigar a diferença entre potencial de geração renovável regional e capacidade efetiva de conexão, transmissão e confiabilidade. A EPE também afirma que as grandes cargas exigem alta disponibilidade; é preciso separar confiabilidade do suprimento elétrico da redundância interna dos próprios data centers.

**Possível ligação futura:** o artigo #9925 poderá apontar para essa matéria no trecho sobre infraestrutura; a nova matéria deverá retornar ao texto de contexto sobre eficiência e consumo.

**Fonte de origem:** Caderno de Demanda PDE 2036, p. 36; Relatório Síntese PDE 2036, p. 62 e p. 101.

### P2-02 — A água invisível da inteligência artificial: refrigeração, clima e eficiência dos data centers

**Oportunidade:** investigar consumo de água, tecnologias de refrigeração, diferenças climáticas, uso de água por kWh e os requisitos regulatórios brasileiros.

**Valor editorial:** o PDE 2036 explica que clima quente e úmido pode limitar o aproveitamento de ar ou água do ambiente para resfriamento e aumentar a dependência de refrigeração mecânica. Há também um gancho legal concreto: a Lei nº 15.504/2026 institui o Redata e estabelece, para pessoas jurídicas habilitadas ao regime, compromisso de apresentar WUE igual ou inferior a 0,05 L/kWh com aferição anual, além de publicar relatório de sustentabilidade com o WUE e as fontes de eletricidade utilizadas. Isso não é um limite geral para todo data center no país; aplica-se às condições de habilitação ao Redata e deve ser lido junto da regulamentação.

**Possível ligação futura:** conectar essa matéria ao artigo #9925 pela discussão sobre recursos físicos necessários à expansão da IA.

**Fontes de origem:**
- PDE 2036, páginas impressas 67–68 e 153.
- Lei nº 15.504/2026, art. 11-B, §1º, inciso IV, e §10: https://planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/l15504.htm

---

## Novo alerta de apuração material — esclarecer a taxa de 13,7%

A taxa média de 13,7% a.a. aparece tanto no Relatório Síntese quanto no Caderno de Demanda para data centers. A mesma família de documentos apresenta a série de consumo elétrico de 3 TWh (2026), 23 TWh (2031) e 30 TWh (2036). A taxa de crescimento composta calculada entre 3 e 30 TWh em dez anos é cerca de 25,9% a.a., não 13,7%. Isso pode refletir bases/escopos distintos, mas a documentação consultada não deixa a distinção clara. Registrar como pergunta para a EPE, não como acusação de erro. Uma consulta institucional ou LAI deve pedir série, base inicial, período, unidade, definição de “demanda” e vínculo entre a taxa de 13,7% e a projeção em TWh. Até resposta ou esclarecimento documental, não misturar os números no mesmo argumento.

O Relatório Síntese é identificado como versão 1 para Consulta Pública (07/10/2026). O prazo da Consulta Pública MME nº 235 terminou em 06/11/2026, mas a página da EPE consultada ainda identifica o Relatório Síntese como versão para Consulta Pública; não presumir que tenha sido publicada versão final apenas porque o prazo terminou.

## Continuidade editorial e links internos existentes

Busca somente leitura no catálogo de publicações do site encontrou:
- #9687 — “IA nos jogos: por que a rejeição cresce enquanto a tecnologia avança nos chips”: aborda aplicações e aceitação de IA em jogos/hardware, mas não sustenta o argumento energético. Não recomendo inseri-lo neste artigo por mera associação de assunto.
- #9869 — “Pane global da Microsoft afeta Brasil e serviços de saúde no Reino Unido”: aborda disponibilidade de serviços digitais, mas não é evidência sobre confiabilidade da rede elétrica. Pode ser considerado em outro contexto sobre resiliência de serviços, não como suporte ao tema energético.
- #9133 — “CEO da Anthropic pede freio na IA e alerta risco online”: não tem relação direta com o argumento energético.

**Conclusão sobre links:** não foi identificado, na busca realizada, um artigo publicado que aprofunde diretamente data centers, consumo elétrico ou conexão à rede. Não inserir links internos artificiais. Criar as pautas P2 e só ligar os artigos depois que os novos conteúdos existirem e forem publicados.

## Limites deste piloto

- Esta é uma segunda leitura manual, produzida a partir da versão identificada pelo hash acima. Não foi invocado o módulo automático ASVE nem seu provedor de IA.
- Não foi criado recibo oficial do Revisor Único.
- Não houve alteração, comentário, aprovação ou publicação no WordPress.
- A validação factual dos apontamentos utiliza os documentos e links listados; cada afirmação incorporada ao artigo deverá ter seu próprio registro no dossiê de evidências, com localização exata, período, metodologia e limitações.
- Antes de uma execução formal da ASVE, o executor deve reler o post e confirmar que o hash continua sendo `7cdd3e4e3b6abd6d18ced7769c8491f151b517e3ee9539b8ef1f583840354ece`.

