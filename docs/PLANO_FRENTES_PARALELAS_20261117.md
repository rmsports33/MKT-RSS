# Plano de frentes paralelas — Conexo OS / ConexoTech — 17/11/2026

Documento único para trabalho simultâneo em ferramentas diferentes (OpenCode,
ChatGPT, outras instâncias) **sem sobreposição de arquivos, sem duplicidade de
melhoria e sem quebrar produção**.

Regra central: **cada arquivo tem um dono por vez**. Quem não é dono, não edita —
abre pedido e segue na própria frente.

---

## 1. Situação global (estimativa)

Método: 23 itens ativos avaliados (3 adiados por decisão ficam fora), peso por
impacto operacional. Não é medição automática — é estimativa com critério.

| Área | Pronto | O que falta |
|---|---|---|
| Motor editorial (coleta → rascunho) | ~92% | nada estrutural; só rodar |
| Publicação e revisão (Gate) | ~55% | 1 revisão humana real; perfil do revisor |
| Site público (SEO, imagens, layout) | ~60% | título da home, Schema, homologar imagens |
| Infra de execução (servidor, SSH, backup) | ~95% | manter e monitorar |
| Painel | ~85% | revisar e mesclar o PR |
| Higiene e dados antigos | ~45% | 149 rascunhos, preços, branches |
| **Total estimado** | **~80%** | **~20% restante é quase todo humano, não código** |

Conclusão principal: o que falta **não é construir**. É **validar, autorizar e
limpar**. Por isso o gargalo real é a fila de revisão humana, não a engenharia.

---

## 2. Pendências, relevância e dono

| ID | Pendência | Impacto | Bloqueio | Dono |
|----|-----------|---------|----------|------|
| M11 | Publicar 1º artigo aprovado pelo Gate | **Altíssimo** — sem isso o fluxo nunca foi provado de ponta a ponta | Revisão humana de 4 afirmações | Proprietário |
| M12 | Perfil do revisor ID4 no Gate | Alto — sem perfil, o modo "dono aprova" não repete | Tela administrativa autenticada | Proprietário |
| M19 | SEO: título da home + Schema duplicado | Alto — primeira impressão pública e busca | Escrita no WordPress | Proprietário (1 campo) |
| M07 | 149 rascunhos antigos | Médio-alto — polui a fila e a triagem | Falta a lista em JSON | Proprietário roda; OpenCode classifica |
| M20 | Imagens #9705/#9708 | Médio — qualidade visual | Revisão em 390 e 1440 | Proprietário |
| M14 | Preços desatualizados | Médio — confiança e SEO | Auditoria ao vivo | OpenCode prepara (só leitura) |
| M15 | Painel: dependências | Médio — segurança | Revisar e mesclar PR #1 | Proprietário |
| M25 | Branches velhas no GitHub | Baixo-médio — organização | Autorização | Proprietário |
| M16/M23/M24 | Bot, staging, Ollama/Actions | Nenhum agora | Adiados por decisão | — |

---

## 3. Frentes isoladas (o coração do plano)

Cada frente tem **pasta própria**. Duas frentes nunca editam a mesma pasta.

| Frente | Escopo de arquivos | Ferramenta sugerida | Pode | Não pode |
|--------|--------------------|--------------------|------|----------|
| **F1 — Site e layout** | repo `-site-conexotech` (tema), WordPress via MCP | ChatGPT / design | CSS, tema, imagens, metadados | Tocar em `mkt_flow_p0/` ou `tools/` |
| **F2 — Motor editorial** | `mkt_flow_p0/`, `pipeline_rss.py`, `pipeline_p0.py` | OpenCode | Melhorar geração, prompts, testes próprios | Editar tema, Gate ou servidor |
| **F3 — Publicação e Gate** | `tools/publish_*`, `tools/wp_identity_preflight.py`, Gate PHP no repo privado | OpenCode prepara; humano aprova | Ajustar guards e pré-voo | Publicar ou aprovar |
| **F4 — Dados e insumos** | `docs/`, planilhas, relatórios | ChatGPT | Auditar preços, listar rascunhos, montar planilhas | Alterar código |
| **F5 — Infra e servidor** | `ops/hostinger/`, servidor, credenciais | OpenCode | Deploy, backup, cron, chaves | Mexer em conteúdo editorial |
| **F6 — Higiene** | `docs/`, `tests/`, branches | OpenCode | Documentar, organizar, remover lixo | Alterar regra de negócio |

### Arquivos congelados (ninguém edita sem combinar antes)
`mkt_flow_p0/editorial_transport.py`, `mkt_flow_p0/gate_unified.py`,
`mkt_flow_p0/release_guard.py`, `mkt_flow_p0/origins.py`,
`tools/publish_owner_approved*.py`.
Motivo: qualquer alteração aqui afeta aprovação e publicação ao mesmo tempo.

---

## 4. Regras de convivência (6)

1. **Uma frente = uma branch** com nome `frente/<nome>-<data>`.
2. **Reserva antes de começar**: registrar no quadro (seção 5) qual pasta a frente
   vai usar. Se já houver dono, não começa — escolhe outra tarefa.
3. **Uma melhoria tem um ID** (ex.: `F2-03`). Se aparecer duas vezes, a segunda é
   duplicata e é descartada.
4. **Nunca dois na mesma pasta.** Conflito de arquivo é proibido por desenho.
5. **Toda frente termina com prova**: antes/depois, ou `check` + `apply` + `verify`.
   Sem prova, não conta como concluído.
6. **Integração é fila única**: as frentes produzem branches; só um integrador
   (OpenCode, em sequência) leva para `master`. Nunca dois merges ao mesmo tempo.

---

## 5. Quadro de reservas (preencher antes de trabalhar)

| Frente | Dono | Pasta/branch | Início | Fim | Estado |
|--------|------|--------------|--------|-----|--------|
| F1 | _(livre)_ | | | | |
| F2 | _(livre)_ | | | | |
| F3 | _(livre)_ | | | | |
| F4 | _(livre)_ | | | | |
| F5 | _(livre)_ | | | | |
| F6 | _(livre)_ | | | | |

Regra: só uma linha ativa por frente. Ao terminar, registrar a evidência e liberar.

---

## 6. Ordem de integração (sequencial, segura)

1. F6 (higiene) — não muda comportamento, só organiza.
2. F2 (motor) — testes focados antes.
3. F3 (publicação) — só depois de F2 estável.
4. F5 (infra) — deploy com backup e readback.
5. F1 (site) — visual, reversível, por último.
6. F4 (dados) — contínua, sem merge de código.

---

## 7. Como cada ferramenta entra

- **OpenCode**: executa código, testes, branches, servidor.
- **ChatGPT**: produz texto, análise e material de revisão; recebe a tabela da
  seção 3 como instrução de escopo e **não** altera arquivos de outra frente.
- **Outras instâncias**: mesma regra — reserva no quadro, escopo da tabela 3.

O contrato entre elas é este documento. Não é preciso conversa entre as
ferramentas: basta respeitar dono, escopo e prova.
