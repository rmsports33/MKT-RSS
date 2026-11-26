# PATCH ADITIVO — Registro confiável assinado no Gate V1

**PR #137 — contrato efetivamente implementado e validado.**

## Objetivo

Fazer o Gate V1 RC10.4 devolver `{record, signature}` compatível com
`editorial_trusted_review.verify_independent_review()` do MKT-RSS (PR #136),
sem modificar core RC10.4, MU-plugins ou criar outro Gate.

## Arquivo novo

Copiar para:

```
wp-content/plugins/conexo-editorial-gate/includes/gate_v1_registry_route.php
```

## Única alteração no bootstrap

Em `wp-content/plugins/conexo-editorial-gate/conexo-editorial-gate.php`, dentro de
`cxeg_standard_boot()`, adicionar **uma linha** após o `require_once` de
`conexo-owner-review.php`:

```php
require_once __DIR__ . '/includes/gate_v1_registry_route.php';
```

## Chave separada

`CONEXO_REVIEW_REGISTRY_KEY` (≥32 bytes), distinta de `CONEXO_EDITORIAL_GATE_KEY`.
A rota recusa chave ausente ou repetida (HTTP 503).

## Contrato da rota

`GET /wp-json/conexo/v1/editorial/registry/{id}`

Permissão: revisor/proprietário autorizado (`cxeg_owner_current()` ou executor
`mkt_rss` em `cxeg_broker_authorized_actors`) — **não** apenas `edit_others_posts`.

Resposta (somente com parecer humano vigente e independente):

```json
{
  "record": {
    "reviewer_id": "7",
    "draft_sha256": "<draft_digest() do Python>",
    "decision": "APROVADO",
    "status": "FINAL",
    "independent": true,
    "evidence_refs": ["https://..."],
    "review_record_url": "https://.../wp-json/conexo/v1/editorial/registry/{id}",
    "revoked": false
  },
  "signature": "<HMAC-SHA256 do canonical record com CONEXO_REVIEW_REGISTRY_KEY>"
}
```

### Regras efetivas

| Regra | Implementação |
|-------|---------------|
| Independência | `review_mode` deve ser `independent` (owner rejeitado); `reviewer_id` da qualidade == da aprovação ≠ autor |
| `draft_sha256` | Campos canônicos: `id, status, title, content, slug, categories, featured_media`; `sort_keys`, UTF-8, sem espaços — idêntico ao `draft_digest()` Python. **Não** é o hash do snapshot do Gate |
| Evidências | Somente URLs HTTPS explicitamente registradas em `checks[].evidencia`; HTTP/inválidas rejeitadas; sem evidências → 404 |
| HMAC | `hash_hmac('sha256', canonical_json(record), CONEXO_REVIEW_REGISTRY_KEY)` |
| Segredos | Nunca na resposta, logs ou documentação |
| Sem parecer | HTTP 404 (`cxeg_registry_no_review`) |

## Validação (isolada, sem produção)

| Teste | Resultado |
|-------|-----------|
| `php tests/test_gate_v1_registry_route.php` | 16 asserções PASS |
| `python -m pytest tests/test_gate_v1_registro_cross_language.py` | 4 PASS |
| `python -m pytest tests/test_gate_v1_registry_contract.py` | 2 PASS |
| Suíte MKT-RSS | 1303 PASS; 48 falhas idênticas ao baseline (Windows/SQLite) |

**Teste cruzado PHP → Python:** o envelope produzido pelo PHP é validado com
sucesso por `verify_independent_review()` do Python.

**Não aplicado em produção** — aguardando autorização específica.
