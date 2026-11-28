# Relatório individual de homologação dos quatro PRs — 28/11/2026

Homologação é decisão técnica documental. **Não é autorização de merge, deploy ou produção.**

| PR / repositório | Branch | SHA revisado | Arquivos | Evidências de teste | Riscos / dependências | Decisão do proprietário |
|---|---|---|---:|---|---|---|
| #91 — `-site-conexotech` (Gate V1) | `fix/gate-v1-minimal-versioning-20261127` | `2b7180fa3de66b644372d3661a392852e728661c` | 26 | Clone limpo do GitHub: 7 testes aprovados; PHP lint 0 falhas; 18 `MATCH`, 1 divergência de credencial, 1 divergência documentada de README, 1 duplicata | Checks do PR falham por cobrança do Actions e ausência de config no CircleCI; nenhuma constante/UUID provisionado; não ativar rotas sem autorização | pendente |
| #142 — MKT-RSS | `feat/editorial-quality-score-20261127` | `aee13d928234ebcfeb719e4165909c86a3d7de66` | 41 | 17 testes locais aprovados (12 de scoring + 5 de golden set); evidência anterior de suíte Linux no SHA `4f1f5a0` | Score é diagnóstico, não aprovação; piloto A/B cego pendente; golden set começa vazio; credenciais não usadas | pendente |
| #6 — `bot-redator-artigo` | `docs/editorial-quality-contract-20261126` | `418be3556d15c001e5882e8c345626b0d78ea138` | 4 | 143 testes locais aprovados em evidência anterior; **sem validação Linux** | Runtime ainda em contrato 1.0; v1.1 está no prompt e em `AGENTS.md`; cópia vendorizada no MKT-RSS divergiu | pendente |
| #86 — `conexo-os` | `feat/editorial-quality-contract-20261126` | `c22f1dd8b2e9dc8d5065261928a8f61ecf51ed3c` | 7 | Sem suíte própria executada nesta etapa;alteração documental registrada | Contrato canônico v1.1 com hash `6b55c87c…`; `main` local está 31 commits atrás do remoto | pendente |

Estado comum: todos abertos, **Draft** e tecnicamente mergeáveis. Nenhum recebeu merge.

## Como preencher a decisão

Para cada PR, registrar: SHA revisado, testes citados, riscos, dependências e uma das saídas:
**homologado como código**, **homologado com ressalvas**, **não homologado**, ou **aguarda evidência**.

A decisão de homologação não autoriza merge. Merge e deploy exigem autorização separada e explícita.

## Estado da etapa

**PARCIAL — aguardando decisão do proprietário.** Relatório preparado; nenhum PR foi mesclado, fechado ou alterado nesta etapa.
