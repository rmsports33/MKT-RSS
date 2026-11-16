# Plano de Unificação do Gate Editorial — 16/11/2026

## Objetivo e não-objetivos

**Objetivo:** consolidar o Gate Editorial em uma única fonte de verdade, eliminar telas duplicadas, padronizar o vocabulário de estágios e garantir que nenhuma aprovação técnica substitua o aceite humano emitido pelo Gate do WordPress.

**Não-objetivos:**
- Não criar contas/revisores/brokers paralelos.
- Não automatizar assinatura humana (o aceite no ChatGPT é deliberação editorial, não recebo autenticado do Gate).
- Não publicar nem agendar artigos sem o recibo autenticado do Gate.
- Não mexer em master, WordPress, Turso, Hostinger ou deploy automático.

## Invetário D1..D16 — status ao final do Incremento 1

| ID | Duplicação/Lacuna | Evidência (caminho:linha) | Status | O que seria necessário para fechar |
|----|---|---|---|---|
| **D1** | Duas telas de aprovação em dois plugins diferentes (`conexo-editorial-gate` e `conexo-gate-agenda-nativa`) | `rmsports33/-site-conexotech` plugins: `conexo-editorial-gate/conexo-editorial-gate.php` (tela "Revisão do proprietário") e `conexo-gate-agenda-nativa/conexo-gate-agenda-nativa.php` (slug `conexo-gate-revisar-lote`) | **Resolvido** — acesso ao repo privado confirmou dois plugins concorrentes; decisão de produto: manter `conexo-owner-review` como tela única por versão, tela de lote passa a linkar para ela. | Decisão de produto no repo privado; não afeta o MKT-RSS público. |
| **D2** | Dois transports de escrita (`mkt_flow_p0/editorial_transport.py` `publish_package` vs `mkt_flow_p0/editorial_broker_transport.py` `publish_via_broker`) selecionados por `CONEXO_EDITORIAL_TRANSPORT` | `mkt_flow_p0/editorial_transport.py`, `mkt_flow_p0/editorial_broker_transport.py` | **Em progresso** — o broker/write permanece como único caminho de publicação; o transporte draft-only `wp_draft_staging.py` continua como alternativa offline. | Definir política canônica de transporte no repo público; o private repo decide qual fica ativo. |
| **D3** | Três implementações do "versão owner-approved" (`tools/publish_owner_approved.py`, `tools/publish_owner_approved_batch.py`, `gate_owner_version` no broker) | `tools/publish_owner_approved.py`, `tools/publish_owner_approved_batch.py`, `mkt_flow_p0/editorial_broker_transport.py` | **Resolvido** — as três tools agora delegam a `gate_unified.py` (`read_owner_release`, `validate_owner_release`, `build_release_trace`). Fonte única: receio do servidor, nunca hash colado. | Manter as tools delegando; nenhum novo transport deve pular o gate_unified. |
| **D4** | Quatro vocabularies de estágios (13 checks do Gate, 10 executores em `editorial_trace_gate.py`, 11 traces WP em `conexo_gate_trace.py`, 9 receipts advisory em `editorial_voice_adapter.py`) | `mkt_flow_p0/gate_unified.py` `CHECK_STAGES`, `mkt_flow_p0/editorial_trace_gate.py`, `mkt_flow_p0/conexo_gate_trace.py`, `mkt_flow_p0/editorial_voice_adapter.py` | **Resolvido** — `CHECK_STAGES` no gate_unified cobre todos os 13 checks; `titulo`, `categoria` e `html` agora suportam estágio (`editorial_approval`, `render_review`) — antes podiam ser marcados sem bloquear nada. | Manter retrocompatibilidade; futuras adições de estágio seguem o mapa canônico. |
| **D5** | Quatro variantes de prontidão com nomes quase idênticos (`conteudo`, `wordpress`, `recibos`, `ambiente`) | `mkt_flow_p0/gate_unified.py` `readiness_catalog` | **Resolvido** — `readiness_catalog` nomeia explicitamente as 4 prontidões e seus significados. | Documentar quando cada variante deve ser usada; não criar novas variantes sem agregação de valor. |
| **D6** | Três definições de "digest" de texto (`content_digest` paralelas no broker, gate, schedule) | `mkt_flow_p0/gate_unified.py` `content_digest`, `mkt_flow_p0/editorial_broker_transport.py` (antes `hashlib.sha256` inline) | **Resolvido** — `content_digest` no `gate_unified` é a única definição; broker foi atualizado para importá-la. Qualquer novo digest deve importar de `gate_unified`. | Proibir definição inline de SHA-256 em novos módulos; sempre importar de `gate_unified`. |
| **D7** | Gate de valor `gate_publicacao` inativo via `GATE_PUBLICACAO_ENABLED` em `mkt_flow_p0/content_filter.py` | `mkt_flow_p0/content_filter.py`, `mkt_flow_p0/gate_unified.py` | **Sem alteração** — gate de valor continua inativo; `GATE_PUBLICACAO_ENABLED` permanece false/indisponível. | Se necessário no futuro, gate de valor pode ser reativado seguindo o padrão `gate_unified`. |
| **D8** | Gatelocal sempre-fechado (`editorial_publish_gate.py`, `editorial_publish_transition.py`) não exigia aceite humano do Gate | `editorial_publish_gate.py` (antes não exigia `owner_release`), `editorial_publish_transition.py` | **Resolvido** — `editorial_publish_gate.py` agora exige `owner_release` válido (receio do servidor). Sem o recibo, a publicação continua bloqueada — um check técnico nunca vira aprovação. | Manter a exigência; remover seria reabrir D8. |
| **D9** | Quatro probes read-only lendo o mesmo arquivo PHP do Gate (`gate_stage_preflight.py`, `gate_stage_contract.py`, `gate_receipt_contract.py`, `gate_issuer_discovery.py`) | `ops/hostinger/gate_stage_preflight.py`, `ops/hostinger/gate_stage_contract.py`, `ops/hostinger/gate_receipt_contract.py`, `ops/hostinger/gate_issuer_discovery.py` | **Em progresso** — subagente criado para consolidar lógica compartilhada em `gate_contract_probe.py`; wrappers mantidos como wrappers finos. | Verificar se os 4 wrappers continuam passando testes idênticos após a consolidação. |
| **D10** | Caminho legacy de staging `mkt_flow_p0/wp_draft_staging.py` escrevendo em `/wp/v2/posts` (apenas rascunho) | `mkt_flow_p0/wp_draft_staging.py` | **Sem alteração** — caminho legacy mantido para compatibilidade; não escreve em produção. | Se for remover, precisa de substituição que use o Gate unificado. |
| **D11** | Muitas camadas de prerequisites empilhadas dentro `editorial_transport.publish_package` | `mkt_flow_p0/editorial_transport.py` | **Sem alteração** — layers de prerequisites continuam; `content_digest` agora vem do `gate_unified`. | Auditar periodidade se new prerequisites são adicionadas. |
| **D12** | Docs referenciam workflow `.github/workflows/schedule-wordpress-approved-batch-manual.yml` que não existe; tools `schedule_owner_approved_wordpress.py` e seu teste existem | `docs/WORDPRESS_NATIVE_GATE_SCHEDULING_20261112.md` linha 9, `tools/schedule_owner_approved_wordpress.py` | **Corrigido** — doc agora marca o workflow como removido em 13/11/2026 pela política de publicação imediata; agendamento é manual via hPanel/WordPress Cron. | Manter a nota de superseded; não recriar o workflow sem autoridade do proprietário. |
| **D13** | `CONEXO_GATE_REMEDIATION_AUTO` lido em `wp_draft_staging.py` mas referenciado por nenhum workflow | `mkt_flow_p0/wp_draft_staging.py`, `.github/workflows/` | **Sem alteração** — variável lida mas sem workflow que a use; decisão de manter ou remover pertence ao proprietário. | Se remover, garantir que não quebra fluxo de staging legado. |
| **D14** | O PHP do Gate está fora deste repo (`rmsports33/-site-conexotech`), então é intestável aqui | `tests/test_editorial_transport.py:170` (espera `CXEG_TEST_SITE_ROOT`), PHP do lado do servidor | **Sem alteração** — acesso ao repo privado permite comparação de hash, mas o teste de integração completa exige ambiente PHP. | Comparar SHA-256 do PHP instalado × commit do repo privado como prova de produção = código revisado (não afeta testes Python). |
| **D15** | Três dos treze checks do Gate não sustentavam estágio (podiam ser marcados sem bloquear nada) | `mkt_flow_p0/gate_unified.py` `CHECK_STAGES` — antes a coluna `stage` não existia nos checks `titulo`, `categoria`, `html` | **Resolvido** — `CHECK_STAGES` agora atribui estágio a todos os 13 checks; `titulo`, `categoria` e `html` agora têm suporte a estágio (`editorial_approval`, `render_review`). | Garantir que novas checks também recebam estágio ao serem adicionadas. |
| **D16** | receipt advisory "wordpress_gate_test" exigido por `editorial_voice_adapter.py` mas nada o produzia | `mkt_flow_p0/editorial_voice_adapter.py` `EDITORIAL_REQUIRED_RECEIPTS` (inclui `wordpress_gate_test`), antes não havia função produtora | **Resolvido** — `advisory_gate_receipt()` em `gate_unified.py` agora produce o comprovante vinculando-o ao release do Gate (content_sha256, reviewer, evidence com version_sha256, date). O voice gate passa a aceitá-lo como presente, mas continua fechado quanto à autorização de publicação. | Manter a produção atrelada ao validate_owner_release; não produzir independentemente. |

## Arquitetura alvo

| Área | Definição canônica | Observação |
|---|---|---|
| **Superfície de aprovação** | `conexo-owner-review` como única tela por versão; tela de lote (`conexo-gate-revisar-lote`) só linka para ela | Decisão de produto no repo privado |
| **Vocabulário de checks/stages** | `CHECK_STAGES` canônico em `gate_unified.py`, cobre todos os 13 checks com estágio | `titulo`, `categoria`, `html` agora têm estágio |
| **Leitor de owner-release** | `read_owner_release` lê do servidor (via API WordPress), nunca aceita hash colado | Fonte única e durável |
| **Índice de pendências de aprovação** | `pending_approvals` com link direto para a tela do Gate (sem digitação manual de ID) | Gerado a partir do receipt do servidor |
| **Política de transporte de publicação** | `broker/write` como única via de publicação; escrita client-side HMAC restrita a staging/rascunhos | `rank_math` permanece ativo como fallback público |
| **Nomeação de prontidão** | `readiness_catalog` com 4 variantes explícitas | Não criar variantes sem necessidade comprovada |
| **Digest de texto** | `content_digest()` única em `gate_unified.py`, SHA-256 do texto markdown | Proibir SHA-256 inline em novos módulos |
| **Política de publicação** | Nenhum agendamento (cron Hostinger, GitHub Actions, wp/v2/posts `future`); confirmação humana no Gate inicia publicação imediata; Rank Math ativo como solução corrente | Política desde `EDITORIAL-IMMEDIATE-PUBLICATION-POLICY-20261113.md` |

## Decisões que exigem o proprietário (não são de código)

1. **Qual tela sobrevive** (D1): `conexo-owner-review` (única por versão) ou `conexo-gate-revisar-lote` (lote)? A decisão define o mapa de links entre as telas.
2. **Se o value gate D7 é aposentado**: manutenção como está continua sem impacto operacional.
3. **Se o código de agendamento (D12) é deletado ou mantido como deprecated**: a política atual (13/11/2026) proíbe agendamento automático; manutenção do note histórico fica.
4. **Se a gate de receipts advisory de 9 itens (D16) é aposentada** em favor dos receipts do próprio Gate: a produção atual mantém ambos, o receipt advisory é tradutor, não autorizador.
5. **Confirmação da versão do PHP instalado no servidor** (D14): comparação de SHA-256 do arquivo `conexo-editorial-gate.php` no WordPress × commit do repo privado. Isto é uma prova de integridade, não uma mudança de código.

## Lista de verificação de verificação por item

| Item | Evidência que fecha o item |
|---|---|
| D1 | Hash SHA-256 do PHP instalado × commit do private repo; decisão documentada de qual tela permanece |
| D2 | Política canônica de transporte escrita; transports que pulam `gate_unified` são considerados técnicos debt |
| D3 | `tools/*_owner_approved*.py` todos importam e usam `gate_unified.read_owner_release`; nenhum tem lógica SHA-256 própria |
| D4 | `CHECK_STAGES` cobre todos os 13 checks com coluna `stage`; testes de regressão confirmam |
| D5 | `readiness_catalog` tem 4 entradas; nova entrada só após aprovação do proprietário |
| D6 | Qualquer módulo que calcule SHA-256 de texto importa `content_digest` de `gate_unified`; busca `hashlib.sha256` inline é técnica debt |
| D7 | `GATE_PUBLICACAO_ENABLED` permanece como está; não há ativação sem revisão de produto |
| D8 | `authorize_publish()` exige `owner_release`; testes confirmam bloqueio sem recibo humano |
| D9 | Os 4 wrappers de probe continuam passando `pytest` idêntico; `gate_contract_probe.py` não introduz nova lógica de scraping/leitura |
| D10 | `wp_draft_staging.py` continua sem writes em produção; flag `--dry-run` preservada |
| D11 | `editorial_transport.publish_package` continua com todas as layers; `content_digest` importado de `gate_unified` |
| D12 | Doc `WORDPRESS_NATIVE_GATE_SCHEDULING_20261112.md` marca workflow como superseded; nenhum novo workflow `schedule-*` criado |
| D13 | `CONEXO_GATE_REMEDIATION_AUTO` continua lido mas sem workflow que o use; decisão do proprietário se mantém ou remove |
| D14 | SHA-256 do PHP instalado comparado a um commit do repo privado (exigência de auditoria, não de código) |
| D15 | `CHECK_STAGES` tem estágio para os 13 checks; novo check recebendo estágio segue o mesmo padrão |
| D16 | `advisory_gate_receipt()` produce receipt com `content_sha256`, `reviewer`, `evidence` (com `version_sha256`), `date`; `editorial_readiness` aceita receipt mas bloqueia publicação |

## O que **não pode mudar** (protegido)

- Nenhuma publicação sem aceite humano do Gate (política desde 13/11/2026).
- Master intocada (`f021ea9d`); todas as mudanças ficam em branches de recurso.
- Nenhum deploy do plugin PHP do Gate sem revisão humana no repo privado.
- Receipts e trilha de auditoria preservadas (D3, D16).
- `rank_math` permanece ativo como SEO no modo corrente.
- Gate do WordPress como autoridade única de versão e aprovação.
- Nenhum cron automático de publicação (GitHub Actions, Hostinger Cron, wp/v2/posts `future`).
- `CONEXO_EDITORIAL_TRANSPORT` respeita o broker/write como caminho canônico.