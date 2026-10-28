# Revisão de segurança P1 — Identidade, autorização e integridade (28/10/2026)

## Superfície de risco e decisão

- `--operador` na CLI não prova identidade. A CLI de decisões continua **fail-closed** e não aceita gravações remotas; consulta e histórico continuam disponíveis.
- `mkt_flow_p0/triagem_auth.py` implementa política de **allowlist não vazia** para ator do GitHub e valida repositório, branch `master` e evento manual `workflow_dispatch`. Cobertura de allow/deny em `tests/test_rss_triage_security.py`. **Importante:** `GITHUB_ACTOR` e demais variáveis de ambiente, isoladamente, **não são autenticação criptográfica**. Usar essa política somente em workflow confiável com restrição de environment, revisão humana e permissões mínimas. Nenhum workflow de escrita foi habilitado por esta entrega.
- `rss_triage_audit`: triggers SQLite/Turso `BEFORE UPDATE` e `BEFORE DELETE` impedem alterações acidentais ou via DML comum; testes offline comprovam falha. **Limite:** uma credencial com privilégios de DDL pode remover triggers/tabelas; controles reais de imutabilidade exigem privilégios segregados, auditoria externa ou infraestrutura que impeça DDL. Não atribuir segurança contra administradores do banco a esses triggers.
- O registro de auditoria continua acoplado ao UPDATE de estado para garantir atomicidade no cenário testado. Um cliente com acesso direto ao DB pode contornar o fluxo e modificar `rss_pautas`; a interface de comando não é uma barreira contra essas credenciais.

## Política de acesso antes de liberar escrita real

1. Fluxo de decisão deverá executar em workflow aprovado, na branch `master`, nunca a partir de código `pull_request` não confiável.
2. Configurar `P1_AUTHORIZED_ACTORS` com uma lista nominativa explícita; nunca permitir vazio ou wildcard. Identificar o GitHub actor proveniente do contexto autenticado da plataforma, não de parâmetros fornecidos pelo operador.
3. Para escrita, exigir aprovação humana e vínculo ao ID/ação/justificativa da pauta específica; evitar aprovação genérica reutilizável, `workflow_dispatch` de terceiros e logs de tokens.
4. Usar credencial de homologação restrita, idealmente sem DDL depois da preparação do esquema. Implementar mecanismos de auditoria externos caso seja exigida resistência a administrador do banco.
5. Não modificar as três pautas RSS reais: testes de escrita somente com IDs sintéticos; homologação de seleção sintética anterior foi concluída, mas não equivale à certificação de autorização de operador.

## Critérios para próxima integração

- CI verde no HEAD com testes de permissão aceita/negada, tentativa de edição e remoção da auditoria.
- Revisão do risco de bypass por conexão direta ao banco e do modelo de credenciais.
- Não criar rotina automática, cron, deploy, WordPress ou merge sem decisão separada.

**Status:** implementação de restrições e testes na branch do PR #31. Autorização ponta a ponta permanece **não habilitada** até existir workflow confiável com aprovação e identidade da plataforma.
