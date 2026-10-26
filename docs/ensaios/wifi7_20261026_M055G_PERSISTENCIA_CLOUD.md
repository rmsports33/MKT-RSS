# M05.5-G — Persistência de orçamento cloud-first: decisão de segurança
Data 2026-10-26. PR #20. Estado: NÃO CERTIFICADO para chamadas reais.

## Evidências
- CI da branch antes desta mudança: https://github.com/rmsports33/MKT-RSS/actions/runs/40335768229 — 548 testes MKT-RSS e 52 testes do redator aprovados.
- Workflow editorial: https://github.com/rmsports33/MKT-RSS/actions/runs/40335769297 — success.
- A implementação atual cloud_budget_ledger.py usa SQLite e BEGIN IMMEDIATE, atômico para processos apontando ao mesmo arquivo SQLite; runner GitHub-hosted é efêmero e **não compartilha arquivo entre execuções**.
- Mitigação implementada: sob GITHUB_ACTIONS=true, qualquer tentativa de reserva retorna bloqueio mesmo se o usuário indicar caminho local. Teste de regressão verifica que não grava no ledger.
- Esta mitigação NÃO substitui persistência compartilhada; impede aprovação enganosa.

## Avaliação de alternativas
1. GitHub Actions + artifact/cache: não são transação atômica de reserva; cache/artifacts não oferecem garantias de consistência concorrente nem orçamento global; NÃO APROVADO.
2. GitHub Contents em branch dedicada: atualização de arquivo não equivale a operação compare-and-swap durável com trava global entre jobs; não assumir atomicidade; NÃO APROVADO sem mecanismo adicional comprovado.
3. Serviço transacional remoto já existente (Postgres/Redis com operação atômica, autenticação restrita, backup/limites): candidato, mas disponibilidade, custos e permissões NÃO VERIFICADOS; não provisionar sem aprovação.
4. Execução única sem concorrência, orçamento por tarefa e limite do provedor: alternativa apenas para piloto específico, após confirmação de cota e ausência de faturamento, NÃO equivale a teto diário agregado. 
5. Codex Cloud/ChatGPT Work: ambientes de desenvolvimento, não ledger persistente transacional por si só.

## Critérios de aceitação para backend compartilhado
- Operação atômica reserve-or-reject no servidor; isolamento de concorrência entre máquinas/runs.
- Chave de idempotência por tentativa de chamada; limite diário em UTC e teto por execução.
- Falha fechada por indisponibilidade ou credenciais insuficientes, auditoria mínima sem segredos.
- Testes simultâneos em runners distintos e confirmação da política de custos/uso antes de Groq.
- Não alterar WP, não reativar publicação ou merges.

## Conclusão
Não foi encontrada ou validada uma persistência compartilhada sem custos adicionais nesta etapa. O caminho seguro é BLOQUEAR as chamadas reais do piloto no GitHub Actions até configurar backend apropriado ou escopo supervisionado explicitamente aprovado.
