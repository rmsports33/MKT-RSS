# Adoção proposta das diretrizes fundacionais do Conexo OS

Estado: proposta isolada para revisão; não altera executores, prompts, workflows, gates ou publicação.

Fonte de coordenação: [PR #22 do conexo-os](https://github.com/rmsports33/conexo-os/pull/22). Antes de aplicar, conferir a versão efetivamente integrada à branch padrão.

## Conciliação local
- A regra vigente em `AGENTS.md` manda pesquisar ferramentas alternativas em toda tarefa. Preservá-la até revisão explícita, mas registrar quais soluções existentes, auditorias e componentes foram considerados antes de recomendar adoção; não assumir instalação ou custo.
- Priorizar fluxo editorial do ConexoTech e reaproveitar capacidade existente, sem perder verificação factual e segurança.
- Nenhuma política documental autoriza coleta externa, alteração de credenciais, publicação, merge ou ativação de agendamentos.
- Antes de mudar o pipeline, mapear entradas, consumidores, contratos de evidências, gates e testes de regressão; registrar branch/SHA, critérios de aceite e resultados comprovados.
- Separar `PASS` estrutural de verificação factual real. Produto, preço, data e fonte precisam de evidência correspondente.
- Validar em ambiente isolado: RSS → pesquisa/fonte → payload editorial, sem escrita WordPress. Planejar integrações apenas depois de aprovação do contrato comum.

## Critérios de aceite para adoção executável
1. Identificar regras conflitantes por arquivo, com decisão explícita de precedência.
2. Reutilizar testes e auditores existentes, sem duplicar módulos.
3. Acrescentar testes de compatibilidade com consumidores reais; não declarar implantação com base neste documento.
4. Obter revisão independente e PR dedicado antes de qualquer mudança operacional.
