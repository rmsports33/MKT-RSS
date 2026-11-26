# FASE 1 — GATE V1 LAYOUT NATIVO (26/11/2026)

**Branch:** `feat/gate-v1-layout-nativo-20261126` (base: master `101fe18`)

## Objetivo
Layout de duas colunas do PR #134 **sem lógica paralela**: aproveitar apenas o visual,
usando os mecanismos nativos do Gate V1 para aprovação, hash, nonce, histórico e publicação.

## O que foi feito
| Item | Status | Evidência |
|------|--------|-----------|
| Layout de duas colunas | ✅ | CSS + template |
| Lista com miniaturas, datas e status | ✅ | `cxgv1nat_list_drafts()` |
| Preview dinâmico | ✅ | JS via endpoint nativo `/snapshot/{id}` |
| Botões APROVAR E PUBLICAR / NÃO APROVAR | ✅ | Template |
| Motivos (14) e justificativa | ✅ | `cxgv1nat_rejection_reasons()` |
| Salvamento com mecanismos nativos | ✅ | `cxeg_owner_approve()` + `cxeg_review_` |
| Sem endpoints REST novos | ✅ | Teste Python |
| Sem filas próprias | ✅ | Teste Python |
| Sem modificar core / MU-plugins | ✅ | Teste Python |
| Sem Gate V2 | ✅ | — |

## Testes
| Suíte | Resultado |
|-------|-----------|
| `tests/test_gate_v1_layout_nativo.py` (11 testes) | ✅ 11 PASS |
| `tests/test_gate_v1_layout_nativo.php` (13 asserções) | ✅ 13 PASS |
| Sintaxe PHP (`php -l`) | ✅ OK |

## O que NÃO foi feito
- ❌ Merge, deploy, upload, escrita em produção
- ❌ Ativar/desativar/substituir plugins
- ❌ Modificar MU-plugins ou reescrever core
- ❌ Criar Gate V2
