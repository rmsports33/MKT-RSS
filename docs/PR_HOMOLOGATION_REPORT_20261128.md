# Relatório individual de homologação dos quatro PRs — 28/11/2026

Homologação é decisão técnica documental. **Não é autorização de merge, deploy, ativação ou produção.**

| PR / repositório | SHA revisado | Arquivos | Evidências no SHA | Riscos / dependências | Recomendação do OpenCode | Decisão do proprietário |
|---|---|---:|---|---|---|---|
| #91 — `-site-conexotech` (Gate V1) | `3796bcf5185695a9ab8f0392a390225d9418b4e0` | 29 | Clone limpo: 10 testes aprovados; PHP lint 0; 17 `MATCH`, 2 divergências documentadas, 1 credencial, 1 duplicata | Consumidor ASVE pelo parecer privado, não pelo manifesto; sidecar obrigatório bloqueia quando declarado; rotas desativadas; sem WordPress real | **Homologar com ressalvas**: aceitar como código vigente; não ativar rotas nem provisionar nada | **Homologado com ressalvas** — decisão do proprietário em 28/11/2026 |
| #142 — MKT-RSS | `2761f4ecf6416cd62c5f281087971723efbe1714` (documento em `f93c53a`) | 50 | 43 testes focados aprovados, 1 ignorado, 20 subtests; matriz integrada aprovada; suíte completa: 1544 aprovados e 8 falhas de plataforma Windows | Falhas Windows classificadas como ambientais; piloto humano e A/B cego pendentes; nota 0–100 é diagnóstica | **Homologar com ressalvas**: aceitar código e contratos; não promover limiar editorial sem decisão humana | **Homologado com ressalvas** — decisão do proprietário em 28/11/2026 |
| #6 — `bot-redator-artigo` | `418be3556d15c001e5882e8c345626b0d78ea138` (documento em `f514e5d`) | 4 | Linux validado: 16 testes focados e 143 completos aprovados em `python:3.11-slim`/WSL2; sem credenciais reais | Runtime ainda em contrato 1.0; v1.1 está em prompt/`AGENTS.md`; cópia vendorizada divergente | **Homologar como código**: evidência Linux concluída; merge só com autorização separada | **Homologado como código** — decisão do proprietário em 28/11/2026 |
| #86 — `conexo-os` | `c22f1dd8b2e9dc8d5065261928a8f61ecf51ed3c` | 7 | 154 testes aprovados, 1 ignorado, 69 subtests; contrato e catálogo sincronizados | `main` local 31 commits atrás do remoto; alterações locais não commitadas preservadas | **Homologar como código** | **Homologado como código** — decisão do proprietário em 28/11/2026 |

Estado comum: todos abertos, **Draft** e tecnicamente mergeáveis. Nenhum recebeu merge.

## Como registrar a decisão

Preencher a última coluna com uma das saídas:
**homologado como código**, **homologado com ressalvas**, **não homologado**, **aguarda evidência**.

A decisão de homologação não autoriza merge. Merge, deploy e ativação exigem autorização separada e explícita.

## Estado da etapa

**DECISÃO REGISTRADA:** #91 e #142 homologados com ressalvas; #86 e #6 homologados como código. Nenhum PR foi mesclado, fechado, ativado ou implantado. Homologação não autoriza merge ou produção.
