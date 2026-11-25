# CONTRATO DE INTEGRAÇÃO — MKT-RSS ↔ Gate V1

**Data:** 25/11/2026
**Status:** proposta de contrato, baseada em código lido e testes simulados. Nenhuma alteração em produção.

---

## 1. Decisão arquitetural

- O Gate V1 RC10.4 continua sendo o único publicador autorizado.
- O Gate V2 fica arquivado como referência; não há instalação nem integração.
- O MKT-RSS produz, corrige, valida e emite certificado factual.
- O Gate valida o certificado, a revisão humana e autoriza ou bloqueia a escrita.

## 2. Responsabilidades

| Componente | Faz | Não faz |
|------------|-----|---------|
| MKT-RSS | gerar, validar forma/substância/elegância, corrigir, emitir certificado factual, consultar parecer humano | publicar, aprovar, escrever no WordPress diretamente |
| Gate V1 | revisão humana, aprovação, hash, nonce, escrita, readback, recibo | gerar texto, substituir revisão humana |
| WordPress | armazenar e publicar somente via Gate | aceitar escrita de caminhos paralelos |

## 3. Leitura autenticada do parecer humano

Implementada em `mkt_flow_p0/gate_review_reader.py`.

Rota: `GET /wp-json/conexo/v1/editorial/quality/{id}`
Autenticação: Application Password do executor (`WP_USER` / `WP_APP_PASSWORD`).

Campos validados:
- `valid_for_current_version == True`
- `report.schema == conexo-article-quality/1`
- `report.veredito == APTO_PARA_APROVACAO`
- `report.post_id == post_id` e `body.post_id == post_id`
- `report.snapshot_sha256` (64 hex) opcionalmente comparado ao hash esperado
- `report.reviewer_id` > 0
- `report.reviewed_at` > 0
- `report.review_mode` em `independent|owner`
- `report.checks` não vazio, cada item com `estado=VERIFICADO` e `evidencia` não vazia

Fail-closed: 401, 403, erro de rede, JSON inválido, registro ausente, versão obsoleta, divergência de post/hash, revisor ausente ou evidência faltante.

**17 testes simulados aprovados** (`tests/test_gate_review_reader.py`). Nenhuma chamada REST real.

## 4. Certificado factual

Já existe em `editorial_factual_certificate.py`:
- `draft_digest(post)` — hash canônico do rascunho
- `issue_factual_certificate(post, review_record, key, ...)` — emite
- `verify_factual_certificate(...)` — verifica assinatura, hash, decisão, TTL, revisão, evidências

**18 testes aprovados** na branch `feat/mkt-rss-factual-certificate-integration-20261125` (SHA `c8ec70f`).

Pendência: conectar o emissor ao `gate_review_reader` e ao fluxo editorial real.

## 5. Atomicidade da escrita

Código real lido no Gate V1 RC10.4:
- `cxeg_write` usa `add_option('cxeg_lock_...')` — atômico para o mesmo nonce.
- `cxeg_write_locked` usa `cxeg_op_{nonce}` com estados `RESERVED`/`COMPLETE` e idempotência por ator+assinatura.
- Compara `expected_sha256` antes da escrita e faz readback por hash depois.

**Pendência:** comprovar que nonces distintos no mesmo post não publicam versões divergentes. `editorial_atomic_transition.py` exige `commit_if_unchanged` transacional — ainda desconectado do fluxo real.

## 6. Sequência de integração (a autorizar separadamente)

1. `gate_review_reader` → obter registro humano autenticado
2. `issue_factual_certificate` → emitir certificado ligado ao `snapshot_sha256`
3. `editorial_transport` → `editorial_assessment` **obrigatório e validado antes do desvio wp_broker** (implementado; 6 testes aprovados)
4. `editorial_atomic_transition` → conectado via `gate_certified_publish` (implementado; CAS real ainda deve ser injetado pelo backend do Gate)
5. Gate V1 → certificado validado antes da escrita, sem duplicar aprovação humana (implementado no cliente `gate_certified_publish`)
6. Testes integrados isolados
7. Somente então planejar operação de produção

## 7. Estado atual

| Item | Situação |
|------|----------|
| `gate_review_reader.py` | Implementado, 17 testes simulados |
| Certificado factual | Implementado, 18 testes |
| `editorial_assessment` obrigatório | Implementado no transporte (antes do broker), 6 testes |
| Suíte consolidada local | 46 testes aprovados |
| `gate_certified_publish.py` | Implementado, 6 testes — passos 4 e 5 |
| Backend CAS real | ✅ Implementado no Gate V1 via `wp-content/mu-plugins/conexo-atomic-cas.php` (rota `POST /conexo/v1/editorial/atomic-commit`, 401 anônimo confirmado) |
| Cliente CAS no MKT-RSS | ✅ `gate_cas_backend()` em `gate_certified_publish.py` |
| Suíte consolidada final | 48 testes aprovados |
| PR #133 | Draft; teste de transporte pendente por core externo |
| PR #127 | 80 testes relevantes aprovados |
| Gate V1 RC10.4 | Código lido; rotas e aprovação confirmadas |
| Atomicidade concorrente | Não comprovada |
| Integração final | Não executada |
| Produção | Intocada |

---

**Nenhuma alteração em produção, merge, deploy, publicação ou escrita no WordPress.**
