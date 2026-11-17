# M15 — Painel ConexoTech — dependências — 17/11/2026

## Resultado
- PR #1 (`fix/m0418-panel-deps-contract`), base `main`, atualizado com commit `46dfb65`.
- Next: 16.3.6 → **16.4.6** (versão atual; corrige vuln de runtime).
- Testes de contrato: **8/8 passando** (`npm test`).
- `npm audit`: 14 high restantes, **todas de lint/dev** (`eslint-config-next`,
  `@typescript-eslint/*`, `micromatch`, `fast-glob` etc.) — não afetam runtime/build.
- `npm audit fix --force` **não aplicado**: faria downgrade major do eslint-config-next
  para 14.x (risco de quebrar o painel).

## Decisão
A correção de runtime está feita e testada. As 14 high de dev exigem either
aceitar o downgrade major (não recomendado) ou atualizar o toolchain de lint
numa frente separada — fora do escopo desta correção segura.

PR #1 segue aberto para revisão do proprietário; sem merge automático.
