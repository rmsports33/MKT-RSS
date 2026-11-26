# CARREGAMENTO DO PAINEL PELO GATE V1 — PATCH DE INTEGRAÇÃO

**Objetivo:** comprovar como os 4 arquivos do painel (PR #135) são carregados pelo plugin Gate V1 RC10.4 instalado, **sem modificar o core, os MU-plugins nem criar outro plugin**.

## Arquivos envolvidos (já no repositório MKT-RSS, branch do PR #135)

| Arquivo | Função |
|---------|--------|
| `mkt_flow_p0/gate_v1_layout_nativo.php` | Lógica nativa (lista, preview, aprovação, reprovação) |
| `mkt_flow_p0/gate_v1_layout_nativo_template.php` | Template + hooks (`admin_notices`, `admin_init`) |
| `mkt_flow_p0/gate_v1_layout_nativo.css` | Layout de duas colunas |
| `mkt_flow_p0/gate_v1_layout_nativo.js` | Preview dinâmico + decisão |

## Ponto de carregamento no Gate V1 (arquivo existente)

O bootstrap do plugin é:

```
wp-content/plugins/conexo-editorial-gate/conexo-editorial-gate.php
```

A função `cxeg_standard_boot()` já faz `require_once` dos módulos internos. O carregamento é aditivo: **uma única linha** dentro dessa função, após o `require_once` de `conexo-owner-review.php`:

```php
// Carrega o painel nativo de duas colunas (aditivo, não modifica o core).
require_once __DIR__ . '/includes/gate_v1_layout_nativo.php';
require_once __DIR__ . '/includes/gate_v1_layout_nativo_template.php';
```

As cópias dos arquivos devem ser colocadas em:

```
wp-content/plugins/conexo-editorial-gate/includes/gate_v1_layout_nativo.php
wp-content/plugins/conexo-editorial-gate/includes/gate_v1_layout_nativo_template.php
wp-content/plugins/conexo-editorial-gate/includes/gate_v1_layout_nativo.css
wp-content/plugins/conexo-editorial-gate/includes/gate_v1_layout_nativo.js
```

## Por que é compatível

- O template registra `add_action('admin_notices', ...)` — hook nativo do WordPress que dispara dentro da página `conexo-owner-review`.
- A lógica chama `cxeg_owner_approve()`, `cxeg_snapshot()`, `cxeg_hash()`, `cxgna_draft_readiness()` — funções já existentes no core.
- Nenhuma rota REST nova, nenhuma fila própria, nenhuma substituição de approval.

## Verificação após aplicação (somente leitura)

1. Abrir `wp-admin/tools.php?page=conexo-owner-review&post_id=9906`.
2. Confirmar o cabeçalho "Revisão editorial — layout nativo".
3. Confirmar 3 colunas de estatística e lista à esquerda.

**Nota:** este patch é documentação de integração. Não foi aplicado em produção nesta etapa (sem upload/deploy conforme restrição).

## Diferença: preview dinâmico vs seleção com recarregamento

| Comportamento | Implementado | Motivo |
|---------------|--------------|--------|
| Preview do artigo **atual** sem recarregar | ✅ Sim — `fetch` em `/snapshot/{id}` | Atende ao preview dinâmico |
| Troca para **outro** artigo | Recarrega com `?post_id=novo` | Renova nonce/formulário/hash no servidor (segurança) |

A renovação evita que o formulário nativo (nonce `cxeg_owner_review_{id}`) fique associado ao artigo inicial — risco apontado na revisão. É uma decisão de segurança, não uma ausência de preview dinâmico.
