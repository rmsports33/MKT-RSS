# MDA AUTO → Voz Editorial Adaptativa ConexoTech (piloto controlado)

**Data:** 2026-11-10. **Estado:** implementação técnica integrada à master pelo PR #86 após CI verde (1.104 testes + 52 do redator, validação editorial verde). Comparação A/B cega de artigos completos permanece pendente; a integração não certifica qualidade acima da média nem habilita publicação.

## Fontes verificadas do projeto

- [MDA AUTO — Controlador](../mkt-flow-escrita/MDA_AUTO_Controlador_Autonomo.md): modos automático/assistido/manual, função dos trechos, movimentos intelectuais, contenção epistêmica, análise de divergências, voz autoral que decorre da interpretação, revisão cirúrgica e compressão não destrutiva.
- [Assistente de Escrita Acadêmica](../mkt-flow-escrita/Assistente_de_Escrita_Academica_Prompt_Controlador.md): auditoria contra estrutura uniforme, conectivos mecânicos, ritmo uniforme, conclusões decorativas e polimento sem pensamento.
- [Prompt-Mestre](../mkt-flow-escrita/prompt-mestre%20de%20escrita.md): progressão real do argumento em vez de amontoado de fontes ou variedade artificial de tamanho das frases.
- [README do acervo](../mkt-flow-escrita/README.md): material **documental** do domínio acadêmico, separado do motor MKT-RSS; não há um segundo executável acadêmico a reinstalar.
- [DNA Editorial Conexo OS](https://github.com/rmsports33/conexo-os/blob/main/docs/EDITORIAL_DNA_V1.md): identidade editorial ConexoTech prevalece em todas as saídas.

O acervo não apresenta um catálogo implementado de múltiplas personagens acadêmicas. As lentes deste adaptador são uma proposta nova derivada dos princípios do MDA, não uma restauração literal de funções executáveis antigas.

## Mudança mínima e ponto único de integração

1. O **mesmo briefing canônico** continua com seis campos: genre, reader, need, angle, contribution, limits. Seu contrato e hash permanecem inalterados.
2. O novo módulo puro mkt_flow_p0/editorial_voice_adapter.py fornece editorial_voice_plan(brief) e writing_voice_guidance(brief), sem rede, credenciais, disco ou chamada LLM. As orientações entram pelo editorial_substance.writing_instruction() existente e, portanto, pelo rewriter.montar_prompt() que já atende o MKT-RSS. Não é novo executor.
3. Cada gênero recebe uma lente de abordagem, **não** uma identidade de jornalista fictício: notícia investigativo-documental; guia didático-prática; análise analítico-crítica (ou científico-explicativa quando o recorte contém estudo/pesquisa); comparativo/review comparativo-decisória; nota breve factual-concisa. Há uma seleção explícita opcional e limitada por allowlist para usos futuros, sem alterar o pipeline.
4. O **mesmo revisor assistido** recebe uma rubrica com progressão de ideias, limites, função de fontes, voz fundamentada e atenção a fechamentos decorativos. surface_style_signals() gera apenas pistas de conectivos repetitivos; o próprio resultado declara factual_approval=false e publication_authorized=false. O revisor deve realizar análise semântica; nenhuma heurística textual pode conceder PASS ou bloquear por si só uma decisão editorial.
5. **Custo incremental de chamadas IA: zero** no fluxo existente. O comprimento do prompt aumenta modestamente; isso pode aumentar tokens de entrada da chamada já existente e, portanto, não constitui garantia de custo monetário rigorosamente zero se o provedor tiver tarifa por token. Não há nova geração automática, publicação WordPress, cron, staging ou serviço.
6. Nenhum hash já emitido do DNA_EDITORIAL_PROMPT foi alterado. O plano leva brief_sha256 para comparabilidade e estado ADVISORY_NOT_APPLIED_OR_APPROVED, sem alegar aplicação concluída, autoria humana ou qualidade certificada. Mudança de Markdown continua invalidando a crítica textual anterior.

## Princípios transferidos do MDA AUTO

- **Argumento antes da cosmética:** fatos e relações devem produzir o estilo, não o contrário.
- **Função de cada trecho:** contextualizar, demonstrar, comparar, distinguir, interpretar ou orientar. Cortar apenas conteúdo redundante, preservando nuances.
- **Movimento intelectual:** verificar o que cada seção acrescenta e se cada conclusão é proporcional ao material.
- **Contradição real:** qualificar alegações, sem produzir oposição artificial ou tratar hipótese como certeza.
- **Ritmo proporcional:** evitar monotonia, mas nunca simular espontaneidade com alternância mecânica de frases.
- **Crítica adversarial na mesma chamada já prevista:** perguntas sobre fonte↔alegação, utilidade, fechamento e repetição semântica.
- **Compressão não destrutiva:** eliminar enchimento mantendo limites, trade-offs, informações factuais e interpretações sustentadas.

## Experimento A/B realmente necessário para demonstrar ganho

O corpus de pilotos WordPress já selecionado inclui os rascunhos completos #9798 (guia), #9635 (notícia), #9687 (análise) e #9681 (comparativo). Os textos atuais e revisões anteriores já foram preservados em caderno privado de revisão no Google Drive; **não** publicar manuscritos de rascunho neste repositório.

Para um A/B válido:

- Mesmo assunto, mesmos fatos, mesmas fontes e mesmo orçamento de tokens, distinguindo apenas o prompt do adaptador. Compare com o prompt anterior sem o adaptador.
- Usar a configuração de geração já autorizada, em piloto delimitado, e registrar versão/hash/modelo/insumos. Este PR **não executa Groq**.
- Manter revisores humanos independentes cegos, separar a chave de versões e atribuir notas 0–4 para necessidade, recorte, contribuição, voz e limites. Registrar exemplos e comparações por gênero, não apenas médias.
- Exigir **melhora de contribuição/voz sem regressão factual**, sem tornar manchetes mais sensacionalistas, sem diminuir transparência de fontes e sem alterar personalidade do veículo por acaso.
- O Gate Editorial Único, o controle de imagem e licenças, a revisão factual e a aprovação humana por versão permanecem obrigatórios. Um novo estilo não substitui nenhuma barreira.

## Aceite técnico vs. editorial

**Técnico:** suíte CI verde, seleção de lentes para todos os gêneros, rejeição de campos e instruções arbitrárias, hash do briefing preservado, DNA intacto, cobertura do montar_prompt, triagem não aprovadora e ausência de rede/chamadas extras.

**Editorial:** aguardando comparação A/B de artigos completos por revisor independente. Nenhuma nota criada por IA substitui esse aceite. Não declare qualidade acima da média, deploy WP, publicação nem ganho comprovado antes das evidências.
