# M05.5-F — Reconciliação e revisão técnica do piloto
Data: 2026-10-26. Escopo: PR #20 / MKT-RSS. Revisão estática realizada por assistente, não revisão humana independente.

## Evidência CI
Commit 579b7cee0f7e45b6e66d6959099143048e22f2de:
- CI geral run 40335513609: success.
- Editorial validation run 40335514475: success.
- Runner mantém allowlist original de sete testes. Os novos testes do piloto pertencem à suíte geral, não à lista autorizada do reusable workflow.
- O HEAD pode continuar recebendo outros commits; nunca extrapolar resultado de um SHA para outro.

## Inspeção de riscos
1. **Alto — orçamento não comprovado em cobrança real**. `Policy` aceita tarifas numéricas externas e `_estimate_upper_bound` calcula estimativa; não consulta preços, quotas nem faturamento. Falta bloquear NaN/infinito explicitamente e validar relação entre `max_output_tokens` aprovado e parâmetros realmente usados pelo adaptador.
2. **Alto — callback sem isolamento**. `evaluate(..., generate=callback)` executa qualquer função Python recebida. `wordpress = PROIBIDO` e `escreveu=False` são atributos de relatório; não constituem barreiras de rede ou de sistema operacional contra efeitos colaterais do callback. O processo do runner deve negar rede para WP e secrets WP, e um adapter restrito precisa ser auditado antes de uso real.
3. **Alto — alegações ainda não certificadas**. `check_preview` confronta números literalmente, não valida equivalência de unidade, contexto, afirmações sem números ou autenticidade de fontes. `conflicting_sources=True` é sinal fornecido de fora, não detecção autônoma.
4. **Médio — preço**. O verificador exige presença de preço e data no texto-fonte mas ainda não relaciona de forma estrita o preço, a data, o produto e a loja à alegação publicada. O mesmo preço em contexto diferente poderia escapar.
5. **Médio — campos de saída**. `evaluate` retém apenas título e Markdown em `previsao`; a auditoria de meta, tags, slug, JSON-LD e HTML precisa ocorrer no artefato final, após renderização.
6. **Médio — proveniência**. O hash é da string de entrada, não de um snapshot integral e imutável da resposta HTTP, metadados, timestamps e URL de origem.
7. **Informativo — teste independente**. A CI representa avaliação automatizada remota; não houve revisão independente externa nem prova de factualidade semântica.

## Decisão fail-closed
- Sem conexão do piloto a provider LLM real até corrigir os itens altos, comprovar orçamento/modelo autorizado e restringir o executor.
- Sem criação de rascunho ou publicação WordPress.
- Sem merge/deploy da branch experimental.
- O próximo incremento deve primeiro adicionar testes negativos de `NaN`, infinito, callback com side effects, preço de mesmo valor e data divergente e dado inventado em metadados.
- Revisão independente e validação de fonte→conteúdo final continuam requisitos.
