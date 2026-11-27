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

**Evidência localizada no documento:**
- Página impressa 60: data centers aparecem com 3 TWh em 2026 e 30 TWh em 2036; o documento também contextualiza essas cargas no conjunto das grandes cargas.
- Página impressa 67: a EPE estima crescimento médio anual de 13,7% para data centers no horizonte até 2036 e descreve ganhos de eficiência em equipamentos de TI, software e sistemas auxiliares.
- Página impressa 67: o documento explica que PUE mede a relação entre o consumo total da instalação e o consumo da carga de TI; por construção, não mede a eficiência energética dos próprios equipamentos de TI.

**Ação recomendada:** citar o PDE 2036 como fonte primária principal, apontando página e seção. Preservar a natureza projetada dos números. Acrescentar a informação de que a própria EPE espera melhorias de eficiência ao mesmo tempo que projeta forte aumento do consumo.

**Fonte de origem:**
- EPE/MME — *Plano Decenal de Expansão de Energia 2036, Relatório Síntese*, outubro de 2026: https://epe.gov.br/sites-pt/publicacoes-dados-abertos/publicacoes/PublicacoesArquivos/publicacao-982/topico-860/PDE%202036_Relat%C3%B3rio%20S%C3%ADntese_rev3_2026-10-08.pdf
- EPE — apresentação do Caderno de Demanda do PDE 2036: https://www.epe.gov.br/pt/imprensa/noticias/pde-projeta-avanco-da-demanda-de-energia-e-ganho-de-espaco-da-eletricidade-ate-2036

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

**Valor editorial:** a EPE registra que data centers de grande porte tendem a buscar conexão à rede básica e exigem elevados níveis de confiabilidade e disponibilidade. O PDE 2036 também distribui os investimentos projetados de data centers de grande porte entre os subsistemas Sudeste/Centro-Oeste, Nordeste e Sul. É uma pauta autônoma que explica por que a localização e o acesso à rede são tão importantes quanto a geração nacional.

**Possível ligação futura:** o artigo #9925 poderá apontar para essa matéria no trecho sobre infraestrutura; a nova matéria deverá retornar ao texto de contexto sobre eficiência e consumo.

**Fonte de origem:** PDE 2036, especialmente páginas impressas 60, 62 e 101.

### P2-02 — A água invisível da inteligência artificial: refrigeração, clima e eficiência dos data centers

**Oportunidade:** investigar consumo de água, tecnologias de refrigeração, diferenças climáticas, uso de água por kWh e os requisitos regulatórios brasileiros.

**Valor editorial:** o PDE 2036 explica que clima quente e úmido pode limitar o aproveitamento de ar ou água do ambiente para resfriamento e aumentar a dependência de refrigeração mecânica. O relatório também menciona compromissos de eficiência hídrica associados ao Redata.

**Possível ligação futura:** conectar essa matéria ao artigo #9925 pela discussão sobre recursos físicos necessários à expansão da IA.

**Fonte de origem:** PDE 2036, capítulos de demanda e infraestrutura; legislação do Redata, a confirmar diretamente no texto legal consolidado antes da pauta virar artigo.

---

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

