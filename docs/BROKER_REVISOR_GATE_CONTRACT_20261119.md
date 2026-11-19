# Contrato Broker–Revisor–Gate

Especificação técnica verificável para integrar o Revisor Único ao caminho de publicação pelo broker Conexo (`conexo/v1/editorial/broker/write`), sem autorizar publicação até que todos os critérios abaixo sejam comprovados.

**Estado:** especificação (não implementada). **Base de código:** master `101fe18ddfcfdd6ee7dfaf356f860be1db54b9ff`. **Branches relevantes:** `fix/revisor-unico-gate-verificacao-20261119` (`fb96e0c1f9f34d86bd40fcd433ef17e827d0dc30`, guard local + registro assinado), `fix/revisor-gate-publish-path-20261119` (`e4276c24843464f53dc5bc2d8992501c4e67b723`, bloqueio intencional do broker), `fix/broker-revisor-guard-tests-20261119` (`e1c33a535233decd48770598c623c90fe2846eb9`). **PR #130** (draft) reúne as duas primeiras e **não** está pronto para integração final.

Este documento **não** autoriza publicação, não define data de ativação, não altera código e **não** reduz nenhuma proteção existente. Suíte verde nunca foi interpretada aqui como autorização de publicação.

## 1. Escopo e não escopo

**Dentro:** contrato de mensagens entre MKT-RSS (cliente), o registro confiável do Revisor Único, o WordPress/Gate (RC10.5) e o broker server-side; ordem de verificação; códigos de bloqueio; testes de segurança; critérios de aceitação para retirar o bloqueio `trusted_factual_review_broker_guard_not_integrated`.

**Fora:** alterar o DNA editorial, trocar de fornecedor/chave, publicar ou agendar conteúdo, ativar cron, integrar o Gate PHP, provisionar homologação real, executar merge.

**Pré-condição operacional:** o bloqueio descrito em `mkt_flow_p0/editorial_transport.py:110-113` **permanece** até a Seção 9 estar cumprida e auditada. Nenhuma mudança deste documento, por si só, reabre `wp_broker`.

## 2. Situação atual verificada (19/11/2026)

| Componente | Estado comprovado |
|---|---|
| Guard local (cliente) | `authorize_publish` exige, sempre, parecer do Revisor verificado contra registro injetado; `{"verified": True}` autodeclarado nunca vale. Commit `a1de816` + `fb96e0c` |
| Registro assinado | `verify_independent_review(post, certificate, signing_key, lookup_review, registry_verification_key, *, now=None)` em `editorial_trusted_review.py`; envelope `{record, signature}` com HMAC-SHA256 de chave distinta (`sign_registry_record`) |
| Broker | `publish_via_broker` verifica origem, intenção, referência humana, pacote canônico, Turso, Gate e somente então escreve; hoje recusa `publish`/`schedule` **antes** de qualquer chamada, com `trusted_factual_review_broker_guard_not_integrated` |
| Gate do WordPress | Autoridade de aceite humano; `conexo-owner-release/1` lido do servidor (`gate_unified.read_owner_release`), nunca hash colado |
| Readback | `assemble_wordpress_context_readback` exige `context=edit` (raw) e `context=view` (rendered) do mesmo post/versão/status; string achatada é rejeitada |
| Testes | Suíte do checkout preparado: 1637 passed, 11 skipped, 0 failed (`fb96e0c`); broker recusa com 2 testes e 2 subtests (`e1c33a5`) |

**Lacuna central:** nenhum destes componentes, sozinho nem em conjunto, garante hoje que o broker server-side tenha feito a própria verificação autenticada antes de escrever. O guard é do cliente; um cliente comprometido ou configurado sem as credenciais corretas falseia preenchimentos — por isso o broker é a fronteira final que precisa implementar este contrato de forma independente.

## 3. Atores e fronteiras de confiança

```
[IAS]            [TRUSTED REGISTRY]                [WordPress / Gate RC10.5]
issuer  ------->  registro + assinatura  <-------   owner-release/1
 (M1)                     (M2)                              (M3)
                                                          ▲
        (M4 edit+view)    (M5 recibo)      (M6 pedido)     │
                            ▲   │                          │
              MKT-RSS (cliente)  └──────── broker ─────────┘
```

| Ator | Fronteira | O que pode e não pode |
|---|---|---|
| Emissor do certificado (IAS) | HMAC própria | Emite certificado de revisão; não lê o WordPress; não publica |
| Registro confiável do Revisor | Par assina/verifica próprio | Devolve registro assinado; revogação e sequência monotônica; não escreve |
| Gate RC10.5 (WP) | Chave privada própria | Emite `owner-release/1`; nunca aceita hash colado; não confia no cliente |
| Broker server-side | Segredo próprio no WP Vault | Verifica M1–M5; pode recusar; não gera texto, não agenda sozinho |
| MKT-RSS (cliente) | Sem segredo de emissão | Transporta M1–M4, exibe recibos; não pode produzir PASS |
| Cron / plugin de deploy | Fora deste contrato | Nunca publica sem M3 válido |

**Regra de ouro:** quem publica carrega o custo de provar. O broker **deve** provar internamente M1–M5 antes de qualquer `POST` editorial; qualquer divergência, timeout, resposta ausente ou não-autenticada bloqueia `publish` e `schedule`.

## 4. Chaves e domínios

Quatro chaves, **distintas**, com rotação independente:

| Chave | Uso | Onde vive | Tamanho mínimo |
|---|---|---|---|
| `K_ISS` | HMAC do certificado (M1) | Segredo de emissão (IAS); cliente só verifica | 32 bytes |
| `K_REG` | HMAC/assimetria do registro (M2) | Serviço de registro; broker e cliente verificam | 32 bytes |
| `K_GATE` | Gate RC10.5 | Vault do WordPress; nunca exposta | — |
| `K_BROKER` | Segredo interno do broker | WP Vault; nunca sai do servidor | 32 bytes |

Nenhuma chave sai de seu domínio. `K_BROKER` não assina nada que o cliente possa forjar; o recibo M5 é informativo, não uma nova autorização.

**Recomendação:** em homologação, validar a troca de HMAC-SHA256 (compatível com `sign_registry_record`) por assinatura asimétrica (Ed25519) para M2, eliminando chave compartilhada entre registro e broker. Qualquer migração não pode enfraquecer o caso HMAC já implementado até haver convergência e rollback comprovado.

## 5. Mensagens (contratos de dados)

Todas as mensagens são JSON UTF-8 canônico (`sort_keys`, `separators=(",",":")`, `allow_nan=False`). Hash e comparação são sempre de bytes canônicos. Campo desconhecido **não** implica confiança.

### M1 — Certificado de revisão independente (existente, inalterado)

| Campo | Validação |
|---|---|
| `version` = `1`, `review_type` = `independent_human` | igualdade exata |
| `draft_sha256` | SHA-256 hex; recalculado de `draft_digest(post)`; exige `status=="draft"`, `categories` válidas contendo `10` e sem `1`, `featured_media` int > 0, `slug` não vazio |
| `decision` = `APROVADO` | igualdade exata |
| `reviewer_id` | string não vazia, ≠ aprovador do Gate |
| `review_record_url` | `https://` obrigatório |
| `evidence_refs` | lista não vazia de `https://` |
| `issued_at`, `expires_at` | epoch int; `issued_at ≤ now < expires_at`; TTL ≤ 86400s |
| `signature` | HMAC-SHA256 hex de M1 sem `signature`; comprimento 64 |

### M2 — Envelope do registro confiável (existente, **endurecido**)

```json
{
  "record": {
    "reviewer_id": "...",
    "review_record_url": "https://...",
    "draft_sha256": "<sha256 do draft edit-context>",
    "decision": "APROVADO",
    "status": "FINAL",
    "independent": true,
    "revoked": false,
    "evidence_refs": ["https://..."],
    "issued_at": 1713900000,
    "registry_seq": 91827,
    "expires_at": 1713907200
  },
  "signature": "<hmac|ed25519 de bytes canônicos do record>",
  "served_at": 1713900005,
  "registry_seq_floor": 91827
}
```

Validações adicionais exigidas:

1. Assinatura verificada com `K_REG` (erro: `review_record_signature_invalid`).
2. `issued_at ≤ now < expires_at` e TTL ≤ 3600s (registro é de consulta, não de aprovação).
3. Atualidade da **resposta**: `served_at` dentro de `[now-120, now+30]`; fora disto, `review_record_stale_response`.
4. Anti-replay por sequência: `registry_seq` monotônico por `review_record_url`; valores ≤ último visto são recusados (`review_record_replay_detected`). Cliente e broker guardam o maior `registry_seq` conhecido por registro.
5. `revoked == false` estritamente; qualquer presença ou tipo errado bloqueia.
6. Campos obrigatórios da nota 1–5 do M1 aplicam-se à igualdade `draft_sha256`.
7. Registro não autoritativo está **sempre** atrasado o suficiente para expirar: ausência de `expires_at`/`registry_seq` bloqueia (`review_record_evidence_missing`).

### M3 — Liberação do responsável (existente, inalterada)

`conexo-owner-release/1`, lido pelo broker do servidor (`/wp-json/conexo/v1/editorial/owner-release/{post_id}`) com a identidade de serviço do cliente apenas para leitura; nunca hash colado. Validações: `owner_id == 3`, `review_mode == "owner"`, 13 checks `VERIFICADO` com evidência não vazia, `version_sha256` igual ao do pacote, post_id igual, `content` igual ao raw persistido. Qualquer falha: bloqueio do Gate, sem escrita.

### M4 — Readback WordPress autenticado

Dois GETs autenticados, ambos com identidade de serviço, `allow_redirects=False`:

- `GET /wp-json/wp/v2/posts/{id}?context=edit` → único lugar que expõe `content.raw`/`title.raw`;
- `GET /{slug}/` ou `context=view` → representação pública (HTML), usada só para comparação e vídeo, **nunca** como fonte de versão.

Correlação obrigatória: mesmo `id`, `modified` idêntico, `status` idêntico, `_conexo_mkt_rss_run_id` igual quando presente nos dois. Divergência: `wordpress_context_version_mismatch`. O `draft_sha256` (M1/M2) deve ser recomputável a partir do objeto `edit` exatamente como `draft_digest()` implementa hoje.

### M5 — Recibo do broker (informativo)

```json
{"status": "verified|idempotent|transport_unknown_inspect|...", 
 "post_id": 0, "nonce": "<hex 32>", "verified": true,
 "retry_automatic": false, "operation_nonce": "<nonce do cliente>"}
```

Nunca contém selo de aprovação novo; sempre declara `retry_automatic: false` em incertezas.

## 6. Ordem de verificação (no broker, antes de qualquer POST editorial)

1. Configuração mínima: `wp_url == https://conexotech.com.br`, identidade de serviço, modo explícito `wp_broker`, intent ∈ {publish, schedule}.
2. Entrada: pacote canônico com `stage == "ready"`, `version_sha256` 64 hex, `payload.wordpress.post_id` int > 0.
3. Turso: trilha exigida (`require_release_trace`) presente e **relida** com `run_id` isolado.
4. Readback autenticado M4; só prossegue se correlacionado e raw íntegro.
5. Certificado M1 válido (assinatura, TTL, `draft_digest` confere com M4).
6. Registro M2 válido (assinatura, TTL, `served_at`, sequência, sem revogação).
7. Gate M3 válido (owner 3, mode owner, 13 checks, vínculo de conteúdo e post).
8. Conferência cruzada: `content_digest(M4.raw)` deve ser recomputado e comparado ao `content_sha256` declarado pelo Gate em M3 (`editorial_publish_gate`/`gate_unified`) e ao `draft_sha256` declarado em M1/M2.
9. Apenas então: escrita com `operation_nonce` único; nonce guardado por 48h; resposta conforme M5.

Nenhuma etapa concede autorização às anteriores; cada falha é terminal e **sem** escrita.

## 7. Códigos de bloqueio

| Código | Etapa | Significado |
|---|---|---|
| `WP_ORIGIN_NOT_ALLOWED` | 1 | origem diferente da homologada |
| `HUMAN_REFERENCE_MISSING` | 1 | sem referência humana verificável |
| `CANONICAL_PACKAGE_INVALID` / `CANONICAL_VERSION_INVALID` | 2 | pacote malformado |
| `TRACE_RUN_ID_MISSING` / `TRACE_*` | 3 | trilha Turso ausente/inválida |
| `WP_READ_OUTCOME_UNKNOWN` / `WP_READ_HTTP_REJECTED` | 4 | readback indisponível |
| `wordpress_context_*_mismatch` | 4 | draft ≠ contexto público correlacionado |
| `trusted_factual_review_missing` | 5–6 | argumentos/certificado/registro ausentes |
| `trusted_factual_review_certificate_invalid` | 5 | assinatura/TTL/edição inválidos |
| `review_record_signature_invalid` | 6 | registro forjado/alterado |
| `review_record_stale_response` | 6 | resposta antiga (relógio controlado) |
| `review_record_replay_detected` | 6 | `registry_seq` regressivo |
| `review_record_mismatch` | 6 | decisão/revogação/identidade divergem |
| `gate_owner_release_*` | 7 | Gate ausente/inválido/divergente |
| `remote_version_mismatch` | 8 | conteúdo editado após aceite |
| `trusted_factual_review_broker_guard_not_integrated` | — | **marca do estado atual**; só pode ser removida após a Seção 9 |

## 8. Testes de segurança (obrigatórios antes de retirar o bloqueio)

Convenção: todos os testes são offline, com HTTP mockado e `POST` gravado em espião; **nenhum teste pode publicar de verdade**. `requests.post` chamado zero vezes em 100% dos casos negativos.

| ID | Cenário | Esperado |
|---|---|---|
| SEC-01 | Sem certificado | bloqueio `trusted_factual_review_missing` |
| SEC-02 | Certificado assinado com chave errada | `certificate_invalid` |
| SEC-03 | Certificado expirado (`now > expires_at`) | `certificate_invalid` |
| SEC-04 | Certificado `decision = REJEITADO` | `certificate_invalid` |
| SEC-05 | Certificado `review_type != independent_human` | `certificate_invalid` |
| SEC-06 | Certificado `draft_sha256` de outro draft | `certificate_invalid` |
| SEC-07 | Envelope sem signature | `review_record_signature_missing` |
| SEC-08 | Envelope adulterado (1 byte do record) | `review_record_signature_invalid` |
| SEC-09 | Envelope assinado com `K_ISS` em vez de `K_REG` | `review_record_signature_invalid` |
| SEC-10 | `served_at` agora−300s | `review_record_stale_response` |
| SEC-11 | `served_at` futuro além de +30s | `review_record_stale_response` |
| SEC-12 | `registry_seq` menor que já visto | `review_record_replay_detected` |
| SEC-13 | Registro com `revoked: true` (assinado) | `review_record_mismatch` |
| SEC-14 | Registro com `status: PENDING` | `review_record_mismatch` |
| SEC-15 | Registro com `independent: false` | `review_record_mismatch` |
| SEC-16 | Registro sem `expires_at`/`registry_seq` | `review_record_evidence_missing` |
| SEC-17 | Readback edit e view com `modified` diferentes | `wordpress_context_version_mismatch` |
| SEC-18 | String de conteúdo achatada como raw | `wordpress_content_raw_unavailable` |
| SEC-19 | Gate sem owner-release | `gate_owner_release_missing` |
| SEC-20 | owner-release de outro post | `gate_owner_release_post_mismatch` |
| SEC-21 | Conteúdo alterado após aceite | `remote_version_mismatch` |
| SEC-22 | `owner_id = 4` | `gate_owner_release_invalid` |
| SEC-23 | Check sem evidência no release | `gate_owner_release_invalid` |
| SEC-24 | HTTP 200 com pacote inválido | falha semântica, sem POST |
| SEC-25 | Replay do mesmo `operation_nonce` | segunda tentativa recusada, 1 escrita no máximo |
| SEC-26 | Falha de rede no readback | `WP_READ_OUTCOME_UNKNOWN`, POST não chamado |
| SEC-27 | Timeout no registro | `trusted_review_unavailable`, sem POST |
| SEC-28 | `publish` e `schedule` com modo `wp_broker` | recusa `trusted_factual_review_broker_guard_not_integrated` **até** Seção 9 concluída |

Suíte de integração (homologação): banco isolado + WP de homologação + espelho do registro; executar os 28 casos e 5 positivos (cadeia completa válida; idempotência no retry; rollback restaura conteúdo e status; restauração de backup integra; revisão humana confirma). Nenhum teste em produção.

## 9. Critérios de aceitação (retirar o bloqueio só após todos)

1. 28/28 SEC, 5 positivos e idempotência/rollback verdes no ambiente de homologação do WP, com leituras `context=edit` e pública reais.
2. Suíte completa do repositório verde no checkout preparado, com SHA registrado em `docs/REGISTRO_UNICO_20261118.md`.
3. Rollback de código comprovado (revert para o estado pré-bloqueio ou para `e4276c2`) e restauração de banco/tema/plugins testada a partir de um backup verificável datado.
4. Chaves `K_REG` e `K_BROKER` provisionadas só no servidor; cliente sem elas; sem elas em qualquer commit.
5. Revisão humana do proprietário do código, do Gate e do fluxo de publicação; aceite explícito vinculado à versão exata.
6. PR #130 aberto com escopo mínimo, sem merge automático, sem deploy automático, sem cron.
7. Documento de homologação atualizado no Registro Único (seção própria), com evidências de HTTP, hashes e restauração.

## 10. Ordem de trabalho

1. **Fase A — especificação (este documento).** Nenhum código.
2. **Fase B — registro e teste negativo:** implementar SEC-01…SEC-28 na suíte preparada (offline), sem tocar `editorial_transport.py`.
3. **Fase C — broker e cliente:** verificação independente no broker, nonce store, readback autenticado interno, M2 com sequência e `served_at`.
4. **Fase D — homologação:** banco isolado, dados descartáveis, backup antes/depois, prova de rollback.
5. **Fase E — decisão de integrar:** só com os 7 critérios da Seção 9; PR #130 deixa de ser draft e é integrado no máximo por fast-forward, sem publicação.

## 11. Riscos e questões abertas

- Falta serviço/local real do registro assinado, com `registry_seq` e chave própria; sem ele o broker só pode confiar em mocks.
- Rotação de `K_REG` sem janela de downtime e sem aceitar envelopes de versões antigas.
- Relógio do servidor da Hostinger vs WP vs cliente: skew de relógio precisa ser medido, não assumido.
- Nonce store persistente (ex.: tabela ou opção do WordPress com TTL) — ainda inexistente.
- Homologação sem ambiente WordPress com identificadores descartáveis: impossível provar M4 real hoje.
- Custo de latência: 4 GETs + verificação por publicação; aceitável apenas se a taxa de erro for conhecida.
- Owner `owner_id == 3` confidencialidade: não copiar valores para logs, nem para o Registro Único.

## 12. Definição de pronto para este contrato

- [ ] Todos os testes SEC verdes na suíte preparada;
- [ ] 5 testes positivos com leitura `context=edit` real em homologação;
- [ ] Chave independente do registro provisionada só no servidor;
- [ ] Nenhuma escrita no WordPress de produção durante validação;
- [ ] Rollback e restauração comprovados com backup datado;
- [ ] Aceite humano do proprietário vinculado à versão;
- [ ] Registro Único atualizado (nova seção).

## 13. Apêndice — comandos de verificação rápida

```powershell
python -m pytest tests/test_readback_gate_parecer_e2e.py tests/test_editorial_trusted_review.py `
  tests/test_editorial_publish_gate.py tests/test_editorial_broker_transport.py -q
```
```powershell
python tools/check_registro_unico.py
```
Hoje ambos passam no checkout preparado, mas **não** retiram `trusted_factual_review_broker_guard_not_integrated` nem autorizam publicação. PASS neste documento significa "provado em ambiente controlado", nunca "publicado".
