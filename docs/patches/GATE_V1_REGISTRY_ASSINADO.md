# PATCH ADITIVO — Registro confiável assinado no Gate V1

**Objetivo:** fazer o Gate V1 RC10.4 devolver `{record, signature}` assinado com
`CONEXO_REVIEW_REGISTRY_KEY`, conforme exigido pelo MKT-RSS.

**Restrições:** não alterar core RC10.4, MU-plugins nem criar outro Gate.

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

Definir `CONEXO_REVIEW_REGISTRY_KEY` no ambiente seguro do WordPress (config fora do
repositório). Distinta de `CONEXO_EDITORIAL_GATE_KEY`.

## Contrato da rota

`GET /wp-json/conexo/v1/editorial/registry/{id}`

Resposta (somente quando há parecer humano vigente):

```json
{
  "record": {
    "reviewer_id": "...",
    "draft_sha256": "...",
    "decision": "APROVADO",
    "status": "FINAL",
    "independent": true,
    "evidence_refs": ["https://..."],
    "review_record_url": "https://.../wp-json/conexo/v1/editorial/registry/{id}",
    "revoked": false
  },
  "signature": "<HMAC-SHA256 do record com CONEXO_REVIEW_REGISTRY_KEY>"
}
```

Sem parecer vigente: HTTP 404 (`cxeg_registry_no_review`).
Sem chave separada: HTTP 503 (`cxeg_registry_key_missing`).

## Verificação somente leitura

```bash
curl -u "$WP_USER:$WP_APP_PASSWORD" \
  "https://conexotech.com.br/wp-json/conexo/v1/editorial/registry/{id}"
```

**Não aplicado em produção nesta etapa** — aguardando autorização específica.
