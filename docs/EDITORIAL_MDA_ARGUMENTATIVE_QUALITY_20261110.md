# Homologação incremental — argumentação decisória ConexoTech / MDA AUTO

**Data:** 10/11/2026. **Escopo:** melhoria da geração e da crítica assistida **dentro do MKT-RSS já existente**. **Estado:** alterações em validação pelo CI; a aceitação editorial externa continua pendente.

## Evidência de origem

- Referência editorial escolhida pelo proprietário: [Canaltech, análise Galaxy S26 FE, 04/11/2026](https://canaltech.com.br/smartphone/galaxy-s26-fe-e-bom-mas-depende-de-desconto-para-fazer-sentido/). Serve como **observação de estrutura de raciocínio**, não modelo de texto nem fonte primária de especificações.
- Síntese aprovada para orientação: [EDITORIAL_REFERENCE_CANALTECH_S26FE_20261110.md](EDITORIAL_REFERENCE_CANALTECH_S26FE_20261110.md).
- Experimento Groq A/B real anterior: [EDITORIAL_MDA_AB_CONTROLLED_20261110.md](EDITORIAL_MDA_AB_CONTROLLED_20261110.md), run #42917583190, quatro pares completos, com diagnósticos assistidos mistos. **A/B permanece congelado, sem parecer humano independente**, e os textos integrais e a chave continuam em armazenamento privado separado.
- O proprietário preferiu as versões B dos quatro artigos, sem conhecer a identidade dos braços; é um **indicador qualitativo**, não evidência de ganho causal, factualidade ou aprovação humana.

## Descoberta editorial transferível

Uma análise com personalidade jornalística não depende de frases características nem de persona inventada. Ela distingue:
1. **Questão/tese relevante** — o que o leitor tenta resolver e qual a posição proporcional às evidências.
2. **Prova e procedência** — documentação oficial, declaração comercial, teste de terceiros, teste próprio comprovado ou hipótese, sem confundi-los.
3. **Consequência concreta** — por que cada atributo altera a experiência, a compreensão ou a decisão.
4. **Contrapeso e alternativa** — quando uma vantagem se torna insuficiente, que evidência falta ou que perfil recebe impacto diferente.
5. **Desfecho condicional** — para quem, sob quais condições e limites a recomendação vale; notícia/nota não precisam emitir veredito comercial.

É um **mapa flexível de movimentos intelectuais**, e não roteiro fixo de cinco subtítulos. Os movimentos variam por gênero e lente no `editorial_voice_adapter.py`.

## Desvios já encontrados e seus controles novos

| Desvio no A/B anterior | Orientação incorporada | Limite que permanece |
| --- | --- | --- |
| Guia: ação contraditória com sintoma do leitor | Para cada procedimento, efeito, perda do recurso, reversibilidade e adequação ao sintoma | Revisão factual dos menus e das dependências ainda é necessária |
| SpaceSail: preço e disponibilidade inferidos de notícia regulatória | Separar certificado, oferta comercial e próximo fato verificável; preço requer fonte, data, mercado e variante | Não inferir cobertura ou contrato de homologação do equipamento |
| IA nos jogos: amostras e hipótese de causalidade generalizadas | Distinguir amostra, estudo, hipótese, correlação e consequências de públicos diferentes | Parecer do revisor sobre causalidade depende de fontes, não de palavras-chave |
| Galaxy A36/A16: capacidade técnica 4K inventada no controle | Cada comparação requer procedência, impacto prático e veredito condicionado; não fingir benchmark ou teste próprio | Confirmar variantes e capacidades em documentação primária |

## Alterações concretas

- **Mesmo redator:** `writing_voice_guidance()` acrescenta, no mesmo prompt e sem etapa extra, cinco movimentos de argumentação ligados ao briefing de seis campos existente. `voice_variant=control` permanece **sem essa orientação**, para permitir comparação de versão.
- **Mesmo revisor assistido:** `review_with_provider()` recebe cinco perguntas por gênero e instrui uma avaliação factual e editorial sustentada em trechos do texto, sem criar nota ou escala adicional. Continuam as cinco notas 0–4 do contrato editorial e a mesma chamada de IA.
- **Sem novo executor, persona, template rígido, benchmark fictício nem aprovação automática.** O plano carrega `brief_sha256` e marca `factual_approval=false` e `publication_authorized=false`. Podem aumentar os tokens do prompt existente; não se promete custo monetário rigorosamente zero em provedor tarifado.
- **Limites legais e de atribuição:** não copiar a redação, tabelas, fotos ou os resultados de laboratório do Canaltech; se testes de terceiros forem usados como fontes em matéria real, eles exigem atribuição.
- **Revisão cega não contaminada:** a preferência do proprietário e os apontamentos deste documento não devem ser enviados ao avaliador independente antes do parecer. Não reescrever os oito textos originais do A/B.

## Matriz de aceitação da mudança

**Engenharia:** suíte verde; seis gêneros corretamente roteados, incluindo análise científica por recorte; contrato de seis campos e hash do DNA intactos; prompt de controle inalterado; prompts MDA com cinco movimentos; revisor com única chamada; nenhuma factualidade/publicação declarada pelo novo plano.

**Editorial ainda a comprovar:** comparar textos integrais novamente sob a **versão nova de prompt** com mesma pauta, fontes e modelo, registrando SHA e custo; revisor humano independente cego; verificar se a tese, a consequência de cada fato, os limites e o veredito melhoraram **sem erro factual novo**. A avaliação original permanece evidência histórica e não pode ser reutilizada como prova de melhoria desta revisão.

**Operação real ainda pendente:** direitos de imagem, exibição responsiva de versões finais e prova controlada do bloqueio WordPress pelo Gate editorial rc5; publicação autorizada por versão somente após critérios humanos e técnicos reais.

### Decisão

A implementação não declara que o MDA melhorou os artigos. Ela materializa o aprendizado sobre **como** a escrita deve ser orientada e criticada, com rastreabilidade técnica; o aceite humano e a prova operacional são marcos distintos.
