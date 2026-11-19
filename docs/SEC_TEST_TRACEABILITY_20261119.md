# Rastreabilidade SEC/POS — Fase B (protocolo Ed25519 e registro autenticado)

Commit validado: `8611b299617d4c20d00c9a02a5ff8d8769aaaa19`, branch `fix/ed25519-review-registry-boundary-20261119`, base `fb96e0c`. Documento de referência: `docs/BROKER_REVISOR_GATE_CONTRACT_20261119.md` v2.3 (`0979579`). Escopo autorizado: Fase B **restrita** a Ed25519 M1/M2 e fronteira autenticada do registro, em branch isolada, testes OFFLINE. Nada de broker, WordPress, Gate PHP, produção, bloqueio ou publicação foi alterado.

## Resultados executados

| Ambiente | Comando | Resultado |
|---|---|---|
| Windows local (Python 3.14) | `pytest tests\test_ed25519_review_contract.py tests\test_editorial_trusted_review.py tests\test_readback_gate_parecer_e2e.py tests\test_editorial_publish_gate.py -q` | 69 passed |
| Windows local (suíte ampla, sem `test_remote_queue_bridge.py` por `fcntl`) | `pytest tests -q --ignore=tests/test_remote_queue_bridge.py` | 1569 passed, 34 falhas preexistentes idênticas à baseline, 1 skipped, 1 error (ambiente Windows) |
| Hostinger, clone isolado `~/mkt-rss-ed25519-phaseb-20261119`, venv do checkout preparado | focados nos quatro arquivos | **69 passed, 0 failed** |
| Hostinger, mesmo clone | `pytest -q` (suíte completa) | **1657 passed, 11 skipped, 52 subtests, 0 failed** |
| Hostinger | `git status` antes/depois | limpo; checkout compartilhado permanece em `e4276c2` |

## Matriz SEC

`NOVO` = implementado e executado neste commit; `PREEXISTENTE` = coberto por teste já existente no baseline; `PENDENTE` = requisito do contrato sem teste executável ainda.

| ID | Requisito resumido | Status | Evidência / teste |
|---|---|---|---|
| SEC-01 | sem M1/certificado | PREEXISTENTE | `tests/test_editorial_publish_gate.py::test_missing_factual_review`; `test_readback_gate_parecer_e2e.py` (lista exata de bloqueios) |
| SEC-02 | chave de emissor errada | NOVO | `test_SEC_02_certificate_signed_by_another_issuer_is_rejected` |
| SEC-03 | certificado expirado | NOVO | `test_SEC_03_expired_certificate_is_rejected` |
| SEC-04 | decisão REJEITADO | NOVO | `test_SEC_04_decision_rejected_is_not_an_approval` |
| SEC-05 | `review_type` errado | NOVO | `test_SEC_05_wrong_review_type_is_rejected` |
| SEC-06 | digest de outro draft | NOVO | `test_SEC_06_certificate_bound_to_another_draft_is_rejected` |
| SEC-07 | envelope sem assinatura | NOVO | `test_SEC_07_envelope_without_signature_is_rejected` |
| SEC-08 | registro adulterado | NOVO | `test_SEC_08_tampered_record_is_rejected` |
| SEC-09 | `served_at` fora da assinatura | NOVO | `test_SEC_09_tampered_served_at_is_rejected` |
| SEC-10 | `registry_seq` fora da assinatura | NOVO | `test_SEC_10_tampered_registry_seq_is_rejected` |
| SEC-11 | chave do registro trocada pela do emissor | NOVO | `test_SEC_11_envelope_signed_with_issuer_key_is_rejected` |
| SEC-12 | resposta antiga | NOVO | `test_SEC_12_stale_served_at_is_rejected` |
| SEC-13 | resposta futura | NOVO | `test_SEC_13_future_served_at_is_rejected` |
| SEC-14 | sequência regressiva | NOVO | `test_SEC_14_registry_sequence_regression_is_rejected` |
| SEC-15 | registro revogado | PREEXISTENTE | `tests/test_editorial_trusted_review.py::test_signed_but_mismatched_record_is_rejected` (`revoked=True`) |
| SEC-16 | `status != FINAL` | PREEXISTENTE | mesmo teste parametrizado (`status=PENDING`) |
| SEC-17 | `independent != True` | PREEXISTENTE | mesmo teste parametrizado (`independent=False`) |
| SEC-18 | sem `expires_at`/evidência | PARCIAL | `verify_registry_envelope` recusa, mas sem teste nominal nesta suíte |
| SEC-19 | E1/E2 divergentes | PREEXISTENTE | `tests/test_editorial_wordpress_adapter.py` (edit/view mismatch) |
| SEC-20 | string achatada como raw | PREEXISTENTE | `test_editorial_wordpress_adapter.py` + `test_editorial_publish_gate.py` |
| SEC-21 | M3 ausente | PREEXISTENTE | `test_gate_local_unification.py::test_publication_without_gate_release_is_blocked` |
| SEC-22 | M3 de outro post | PREEXISTENTE | `test_gate_local_unification.py::test_gate_release_for_another_post_is_blocked` |
| SEC-23 | conteúdo alterado | PREEXISTENTE | `test_edited_content_invalidates_the_gate_release` |
| SEC-24 | HTTP 200 inválido | PREEXISTENTE | `test_http_200_with_invalid_packet_is_not_semantic_validation` |
| SEC-25 | check sem evidência | PREEXISTENTE | validação em `gate_unified.validate_owner_release`, coberta por `test_gate_unified.py` |
| SEC-26 | pacote inválido | PREEXISTENTE | `test_editorial_transport.py` / `test_gate_unified.py` |
| SEC-27 | timeout do registro | PREEXISTENTE | `test_lookup_exception_and_timeout_fail_closed` |
| SEC-28 | falha de rede no readback | PREEXISTENTE | `test_editorial_wordpress_adapter.py` |
| SEC-29 | produção em perfil staging | PENDENTE | allowlist ainda não implementada (Fase C) |
| SEC-30 | mesmo nonce em concorrência | PENDENTE | Fase C (tabela/idempotência do WP) |
| SEC-31 | versão já consumida | PENDENTE | Fase C |
| SEC-32a/b | ausência confirmada × desconhecido | PENDENTE | Fase C |
| SEC-33 | `kid` revogado do Gate | PENDENTE | Fase C (M3 Assinado pelo Gate PHP) |
| SEC-34/35 | skew / `Date` ausente | PENDENTE | Fase C |
| SEC-36 | sequência após reinício | NOVO | `test_SEC_36_accepted_sequence_survives_broker_restart` |
| SEC-37 | meta de nonce ausente | PENDENTE | Fase C |
| SEC-38 | concorrência por versão | PENDENTE | Fase C |
| SEC-39 | concorrência pela mesma sequência | NOVO | `test_SEC_39_two_concurrent_requests_with_same_sequence` |
| SEC-40 | engine InnoDB | PENDENTE | Fase C |
| SEC-41 | queda entre T1 e T2 | PENDENTE | Fase C |
| SEC-42 | conflito na inicialização da sequência | NOVO | `test_SEC_42_duplicate_key_initialization_is_not_a_permissive_update` (emulação offline via store) |

### Testes adicionais sem ID SEC no contrato

- `test_SEC_HAPPY_01_ed25519_certificate_and_registry_envelope` — cadeia válida M1+M2.
- `test_self_asserted_verified_flag_is_never_a_review` — parecer autodeclarado não verifica.
- `test_shared_secret_cannot_verify_an_ed25519_envelope` — bytes secretos não verificam Ed25519.
- `test_missing_sequence_store_fails_closed` — sem store persistente, bloqueia.

## Matriz POS

| ID | Status | Motivo |
|---|---|---|
| POS-01…POS-05 | PENDENTE | dependem de broker, WordPress de homologação e restauração; nenhum foi executado nesta Fase B |

## Limites desta entrega

- Ainda existe caminho HMAC legado em `editorial_factual_certificate.py` e `editorial_trusted_review.py` para compatibilidade com os testes pré-Ed25519; a seleção é explícita por `alg`. Eliminação definitiva depende da Fase C.
- M3 assinado pelo Gate PHP, nonce/idempotência do WordPress, allowlist de origem, skew e todas as garantias de escrita seguem pendentes.
- `trusted_factual_review_broker_guard_not_integrated` continua ativo; PRs #129 e #130 seguem draft; nenhuma publicação, cron, merge ou deploy foi executado.
- Suíte verde prova somente o escopo OFFLINE acima — não completa o contrato v2.3.
