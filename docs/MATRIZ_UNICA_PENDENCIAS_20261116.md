# Matriz Única de Pendências — Conexo OS — 16/11/2026

Consolidação de 4 auditorias cruzadas (6 repositórios GitHub) confrontadas com o
estado real verificado. **Uma única fonte de verdade** para não reabrir problemas
resolvidos, não repetir testes e não misturar frentes.

## Convenção de status

| Status | Significado |
|--------|-------------|
| ✅ **Resolvido e comprovado** | Código + integração + evidência |
| 🟡 **Implementado, não integrado** | Código existe, falta ligar ao fluxo real |
| 🟠 **Integrado, não homologado** | Roda em ambiente isolado, falta prova em produção |
| 🔴 **Bloqueado** | Depende de autorização/ambiente externo |
| ⚪ **Obsoleto/substituído** | Superado por componente atual |
| 🔵 **Adiado por decisão** | Fora do plano atual |

---

## MATRIZ

| ID | Item | Repo / Ref | Status real | Dependência | Próxima ação |
|----|------|-----------|-------------|-------------|--------------|
| M01 | Controlador + ponte Turso + Cron | MKT-RSS PR #123 | ✅ Resolvido | — | Nenhuma (preservar) |
| M02 | Gate Unificado (D1..D16) | MKT-RSS FEAT `6f49043` | ✅ Resolvido | — | Nenhuma (integrado na operacional) |
| M03 | Fila 20 pautas + `queue_list` + triagem | MKT-RSS `b079e5c` | ✅ Resolvido | — | Nenhuma (`TRIAGEM_DESCOBERTA`) |
| M04 | PR #46 (SEO readiness) | MKT-RSS | ✅ Resolvido (MERGED) | — | Nenhuma |
| M05 | PRs #105/#109/#115/#118 (catálogo/Turso) | MKT-RSS | ✅ Resolvido (MERGED) | — | Nenhuma |
| M06 | Marker PRONTO_PARA_REVISAO no produtor | MKT-RSS #111 | ✅ Resolvido — `stage_rss_draft` emite `pronto_para_revisao` do readback (commit `6faa96c`) | — | Nenhuma; 35 testes passando |
| M07 | Reconciliar 149 rascunhos antigos | MKT-RSS #114 | 🟡 Fila de correção criada (`editorial_correction_queue.py`, commit `d988c84`, 25 testes) — classifica `completo/incompleto/de_teste/defasado` a partir de metadados com ID/motivo/responsável; reaproveita `validate_wordpress_readiness` sem novo motor | WordPress ao vivo (metadados dos 149) | Operador fornece a listagem `GET /wp/v2/posts?status=draft,pending`; módulo gera a fila; nenhuma aprovação/publicação automática |
| M08 | Revisor de Qualidade único | MKT-RSS #42 / OS #52 | ✅ Resolvido — `validar_saida` reaproveitado no sinal de prontidão (commit `b0b8256`), sem novo motor | — | Nenhuma; achados bloqueiam prontidão, não aprovam |
| M09 | Erro JS `main.js` linha 230 | site #71 | ✅ Resolvido — delta aplicado no servidor (linha 230 `}` → `});`) com backup `main.js.bak-20261117`; sintaxe validada (pares `()` 192/192, `{}` 65/65, `[]` 13/13); versão 1.6.9 coerente | — | Nenhuma. Não mesclar PR #71/#50 (main.js do repo é artefato binário) |
| M10 | Proteção anti-auto-deploy do tema | site #51 | ✅ Resolvido — proteção já em master (`workflow_dispatch`, `default: false`, sem cron) | — | Nenhuma; ver `FASE1_DIAGNOSTICO_20261117.md` |
| M11 | Rascunho Binance via Gate autenticado | MKT-RSS #121 | 🔴 Bloqueado (3 pré-condições reais descobertas no servidor): (1) **não existe pacote `editorial-workflow/2`** — só o handoff `conexo-editorial-handoff/1`, que o script agora rejeita corretamente (`PUBLISHABLE_PACKAGE_MISSING`); (2) **core editorial ausente** (`editorial_write.py`, commit `b485d91`, SHA `823d97d5...`); (3) credenciais em `wp-editorial.token` (script ajustado para ler). Código corrigido e testado (8 testes) mas **não executado**; `job_id` preservado — NÃO publicar requisição ainda | Pipeline supervisionado gerar pacote + instalar core | Ver `DEPLOY_BINANCE_STAGE_20261117.md` (atualizado) |
| M12 | Artigo #9894 — perfil revisor ID4 | Histórico | 🔴 Gravação do perfil pendente | Usuário | Concluir perfil, verificar fluxo, **não publicar** |
| M13 | Nota editorial 1–10 | OS #49 | ✅ Resolvido — `nota_editorial` heurística anexada ao resultado do staging (commit `586cb9c`), `publicacao_autorizada: False` | — | Nenhuma; não confundir com qualidade factual |
| M14 | Preços desatualizados | site #26 | 🔴 Relatório 01/11 desatualizado | Auditoria nova | Refazer auditoria antes de corrigir |
| M15 | Painel — dependências vulneráveis | conexotech-panel PR #1 | 🟡 PR aberto, versões não confirmadas hoje | Revisão | Validar versões atuais antes de integrar |
| M16 | Bot Redator #3/#1, Runner #4/#3 | vários | 🔵 Adiado (runner é protótipo) | — | Manter em backlog; não virar executor |
| M17 | PR multi-IA (Groq/Gemini/OpenRouter) | MKT-RSS #122 | 🟠 Draft, testes Linux pendentes | Ambiente Linux | Testes + homologação, sem fallback prematuro |
| M18 | Shopee → Turso homolog | MKT-RSS master | 🟠 Código pronto, não executado | Token homolog | `--check → --apply → --verify` |
| M19 | SEO nativo / Rank Math | site #58 (privado) | 🟠 Homologação parcial | Ambiente | Auditoria HTML, readback, rollback; Rank Math ativo |
| M20 | Imagens #9705/#9708 | site | 🟠 Parcial | Revisão visual | Homologação ponta a ponta |
| M21 | Backup recente | site | 🔴 Último 13/11 | Drive/servidor | Executar backup verificável |
| M22 | SSH sem senha | Hostinger | 🔴 Não confirmado | hPanel | Cadastrar chave ED25519 |
| M23 | Staging subdomínio | Hostinger | 🔵 Fora do plano | — | Não recriar/não usar |
| M24 | Ollama, Actions como executor, ChatGPT Work, handoff automático | vários | 🔵 Adiado por decisão | — | Não implementar |
| M25 | Branches remotas obsoletas (stub do Gate + 3 planos) | MKT-RSS | 🟡 Limpeza local feita, remoto pendente | Autorização | Excluir após autorização |
| M26 | Recibo `queue-list-20261116-001` | Hostinger | ✅ Resolvido — processado pelo Cron em 17/11 01:29Z, `PASS`, `READ_ONLY`, sem deploy | — | Nenhuma; fluxo GitHub→Cron→ponte→Turso 100% operacional |

---

## Contagem por status

| Status | Qtd |
|--------|-----|
| ✅ Resolvido e comprovado | 10 |
| 🟡 Implementado, não integrado | 1 |
| 🟠 Integrado, não homologado | 5 |
| 🔴 Bloqueado | 6 |
| ⚪ Obsoleto | 0 |
| 🔵 Adiado por decisão | 4 |

**Atualização 17/11:** M06, M08 e M13 integrados na branch operacional
(commits `6faa96c`, `b0b8256`, `586cb9c`) com 70 testes passando. O sinal de
prontidão do Gate agora nasce do readback autenticado, reaproveita o revisor de
qualidade existente e anexa a nota temática — sem criar novos motores e sem
autorizar publicação.

**Fase 1 concluída (17/11):** M10 ✅ (proteção anti-auto-deploy já em master do
repo privado) e M09 ✅ (JS do tema corrigido no servidor com backup, sintaxe
validada e versão 1.6.9 coerente). O `main.js` versionado no repo é artefato
binário de 72 bytes — **nunca copiar do repo para o servidor**; os PRs #71/#50
devem permanecer abertos até que essa divergência seja reconciliada. Ver
`FASE1_DIAGNOSTICO_20261117.md`.

## Sequência de execução (P0 primeiro, sem reconstruir)

1. **M10 → M09** — confirmar anti-auto-deploy, depois aplicar delta JS
2. **M06 → M08** — ligar prontidão ao produtor; confirmar Revisor de Qualidade
3. **M26** — verificar recibo `queue-list` (leitura)
4. **M11 → M12** — entregas editoriais bloqueadas (com autorização)
5. **M18 → M17** — homologação Shopee + PR #122 (sem ativar escrita automática)
6. **M19 → M20 → M21 → M22** — SEO, imagens, backup, SSH
7. **M25** — limpeza remota (com autorização)

**Regra:** nenhuma publicação automática, nenhum segundo Gate, nenhum novo executor,
nenhum merge master↔operacional sem reconciliação. Preservar tudo que funciona.
