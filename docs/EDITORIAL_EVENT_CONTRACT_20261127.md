# Contrato único de eventos editoriais (27/11/2026)

## Princípio

Não criar terceiro sistema de recibos. As implementações já existentes são reaproveitadas:

- `mkt_flow_p0/editorial_trace.py` — envelope `conexo-editorial-executor-events/1`, com `article_id`, `run_id`, `content_sha256` e eventos por estágio.
- Gate V1 PR #137 — `gate_v1_registry_route.php`, envelope `{record, signature}` com HMAC de chave separada.
- Gate V2 — `OperationLedger`, `ReceiptService` e `AuditLog`, com `operation_id`, `receipt_id`, `event_id` e corrente local de eventos.

## Campos obrigatórios do evento

| Campo | Origem | Finalidade |
|---|---|---|
| `article_id` | derivado da URL da pauta | identidade estável do artigo |
| `run_id` | `editorial_trace.py` | identidade da execução |
| `producer` | handoff | `mkt_rss`, `mkt_rss_adapted` ou `external` |
| `origin.kind` | handoff | `RSS_LIVE`, `QUEUED_RSS`, `EXTERNAL_PAUTA` ou `EXTERNAL_CONTENT` |
| `stage` / `module_id` / `module_version` / `status` | eventos da trilha | módulos realmente executados |
| `content_sha256` | sha256 do Markdown/HTML final | ligação com o conteúdo armazenado |
| `version_sha256` | handoff canônico | versão do pacote editorial |
| `evidence_ref` | por estágio | prova verificável, nunca afirmação solta |

## Regras de evidência

`model_id` e `prompt_sha256` **isolados não provam geração**. É exigida correlação entre:

1. produtor declarado;
2. evento `generation` com `status=PASS`;
3. `content_sha256` do texto gerado;
4. `run_id` da trilha;
5. hash do conteúdo lido do WordPress.

Para `producer=external`, o texto é preservado e rotulado como externo; qualquer adaptação pelo MKT-RSS muda o produtor para `mkt_rss_adapted` e exige nova versão/hash.

## Gate

- **Rascunho privado:** exige proveniência verificável, mas não parecer humano.
- **Publicação:** exige todos os estágios aplicáveis da trilha, parecer humano vigente, assinatura do Gate V1 e recibo do Gate V2.

A corrente local do Gate V2 não é blockchain e não é à prova de adulteração; serve como trilha auditável dentro do recibo assinado.
