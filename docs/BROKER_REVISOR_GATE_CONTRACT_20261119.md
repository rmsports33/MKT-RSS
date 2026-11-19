# Contrato Broker–Revisor–Gate — revisão 2

**Versão:** 2.1 (19/11/2026). **Substitui, sem apagar,** a revisão 2.0 em `docs/broker-revisor-gate-contract-20261119.md` no branch `docs/broker-revisor-gate-contract-rev2-20261119`, commit `5b15c719e651f4b467c87954b9da2c7163a52d23`. A v2.0 permanece intacta como histórico; a v1 permanece em `docs/broker-revisor-gate-contract-20261119` @ `9c5b596cd8aaa5fc97b7cb9b189f8ac2d849d284`.

**Finalidade:** especificar, de forma verificável, a integração autenticada entre MKT-RSS (cliente), registro confiável do Revisor Único, Gate RC10.5 (WordPress) e broker `conexo/v1/editorial/broker/write`, **antes** de qualquer retirada do bloqueio `trusted_factual_review_broker_guard_not_integrated`.

**Base de código citada:** master `101fe18ddfcfdd6ee7dfaf356f860be1db54b9ff`; v1 das branches `fix/revisor-unico-gate-verificacao-20261119` (`fb96e0c`), `fix/revisor-gate-publish-path-20261119` (`e4276c2`), `fix/broker-revisor-guard-tests-20261119` (`e1c33a5`). **PR #130:** draft, não pronto para integração final.

Este documento não autoriza publicação, não implementa nada, não retira bloqueio, não cria cron, não faz merge e não implanta. Suíte verde, por si só, não completa a integração.

## 0. Correções desta revisão (bloqueios da revisão técnica)

| # | Bloqueio apontado | Onde foi corrigido |
|---|---|---|
| C1 | HMAC exige segredo compartilhado; verificador também poderia assinar | §2 e §3.1 — Ed25519 para M1, chave pública no verificador; HMAC legado só em servidor de confiança |
| C2 | `served_at`/`registry_seq_floor` fora da assinatura | §3.2 — assinatura cobre envelope completo (`protocol_version`, `alg`, `kid`, `record`, `served_at`, `registry_seq`); `registry_seq_floor` removido |
| C3 | Origem de produção nos testes | §2.3, §4 etapa 1, `SEC-29` — allowlist explícita, produção proibida em homologação |
| C4 | Comparação de digests semanticamente distintos | §5 — definição formal de `draft_digest`, `content_digest` e ponte por igualdade byte a byte; comparação proibida entre digests diferentes |
| A1 | Página pública ≠ `context=view` | §3.4 — E1/E2/E3 separados, campos e correlação próprios |
| A2 | M5 emitido antes da escrita | §1 e §4 — M1–M4 são pré-condições; M5 é recibo **pós-escrita** |
| A3 | Idempotência × replay conflitantes | §4 etapa 9, §6 — três classes de repetição, nonce atômico, `SEC-25`, `SEC-30`–`SEC-33` |
| A4 | `SEC-28` circular | §7.1 — teste temporário `BLOCK-TEMP-01`; testes do contrato implementado separados e expressamente futuros |
| O1 | Cinco positivos não identificados | §7.2 — `POS-01`…`POS-05` com entrada, pré-condição e resultado |
| O2 | Assinatura do Gate M3 | §3.3 — formato, campos assinados, verificação, `kid`, rotação |
| O3 | Autoridade da sequência | §3.2 — `registry_seq` emitido e aplicado apenas pelo servidor do registro |
| O4 | Nonce atômico | §6 — transação, estado, unique key, recuperação após falha |
| O5 | Relógios | §6.1 — medição de skew, janela reavaliada, bloqueio se não sincronizado |
| O6 | Classes de evidência | §8 — offline / homologação real / restauração separadas |
| 2.1-1 | Replay de envelope válido antigo | §3.2 — maior `registry_seq` aceito persistido pelo broker por `review_record_url`, atualização atômica (`CAS`) e `SEC-36` |
| 2.1-2 | Transação local não torna HTTP atômico | §6.2 — reserva persistente, estado `IN_FLIGHT`, nonce no endpoint WordPress, reconciliação; sem alegação de atomicidade distribuída |
| 2.1-3 | Duas operações concorrentes para a mesma versão | §6.2 — restrição única em `(post_id, version_sha256)` para estados ativos e bloqueio transacional; `SEC-38` |
| 2.1-4 | Ausência confirmada × resultado desconhecido | §6.2 e `SEC-32/37` — ausência confirmada permite `FAILED`; leitura inconclusiva mantém `UNKNOWN`/`transport_unknown_inspect` |
| 2.1-5 | Recuperação dependia de meta não listado | §3.4 — `meta._conexo_editorial_operation_nonce` listado e exigido na leitura autenticada de recuperação |
| 2.1-6 | `verified` ambíguo no recibo | §3.5 — estados M5: `published`, `scheduled`, `idempotent`, `transport_unknown_inspect`; `verified` é só validação interna |

## 1. Escopo e não escopo

**Dentro:** contrato de mensagens, ordem de verificação no broker, códigos de bloqueio, testes negativos/positivos e critérios para retirar o bloqueio.

**Fora:** DNA editorial, troca de fornecedor, publicação, agendamento real, ativação de cron, merge, deploy, provisionamento de homologação.

**Regra de estado:** o bloqueio em `mkt_flow_p0/editorial_transport.py:110-113` continua ativo. Pré-condições de escrita são **M1, M2, M3 e M4**. **M5** é o recibo emitido **depois** da escrita; nenhuma especificação pode exigir M5 como pré-condição.

## 2. Atores, chaves e origens

### 2.1 Atores

| Ator | Papel | Pode | Não pode |
|---|---|---|---|
| IAS (emissor do certificado) | Emitir M1 com chave privada de emissão | Assinar decisão de revisão | Escrever no WordPress; verificar publicamente com o mesmo segredo |
| Registro confiável do Revisor | Guardar e assinar M2; sequência autoritativa | Revogar, emitir envelope novo | Confiar em sequência guardada pelo cliente |
| Gate RC10.5 (WP) | Emitir M3 assinado | Aprovar/negar por identidade humana | Aceitar hash colado; publicar diretamente |
| Broker server-side | Fronteira final antes da escrita | Verificar M1–M4, recusar, escrever uma vez com nonce | Gerar texto; confiar em flag do cliente; auto-retry |
| MKT-RSS (cliente) | Transportar mensagens e exibir recibos | Ler, montar pacote, chamar broker | Produzir PASS; verificar assinatura com chave privada |
| Cron/deploy | Fora do contrato | — | Publicar sem M3 válido |

### 2.2 Domínios de chave (separados, nunca reutilizados)

| Chave | Tipo | Uso | Posse | Rotação |
|---|---|---|---|---|
| `K_ISS` | **Ed25519 privada** | Assinar M1 | IAS apenas | `kid` + sobreposição de 24h |
| `K_ISS_PUB` | Ed25519 pública | Verificar M1 | broker (e qualquer verificador) | por `kid` |
| `K_REG` | Ed25519 privada (ou HMAC restrito) | Assinar M2 | serviço de registro apenas | `kid` + sobreposição de 24h |
| `K_REG_PUB` | Ed25519 pública | Verificar M2 | broker e cliente somente-leitura | por `kid` |
| `K_GATE` | Ed25519 privada | Assinar M3 | Gate RC10.5, Vault do WP | `kid` + sobreposição de 24h |
| `K_GATE_PUB` | Ed25519 pública | Verificar M3 | broker | por `kid` |
| `K_BROKER` | Segredo interno | Proteger estado do broker | WP Vault, nunca exportado | administração do WP |

**HMAC legado:** `sign_registry_record`/`verify_factual_certificate` hoje usam HMAC-SHA256. Onde HMAC for mantido temporariamente, a verificação fica **exclusivamente em servidores de confiança**; nenhum cliente externo recebe a chave. Migração para Ed25519 é obrigatória antes da Fase D e não pode ser feita aceitando ambas as chaves no mesmo campo sem `alg` explícito.

### 2.3 Origens (correção C3)

Origens permitidas vêm de allowlist explícita em `CONEXO_BROKER_ALLOWED_ORIGINS`, carregada pelo perfil de execução:

- perfil `staging`: apenas `<HOMOLOGATION_HOST>` (valor real a ser provisionado; **não** é `conexotech.com.br`);
- perfil `production`: apenas `https://conexotech.com.br`;
- allowlist vazia, domínio ausente ou domínio de produção em perfil `staging` → `BROKER_ORIGIN_NOT_ALLOWED`, sem escrita.

Todos os testes OFFLINE e de HOMOLOGAÇÃO usam o perfil `staging`. Teste de produção em modo `staging` é obrigatório (`SEC-29`).

## 3. Mensagens do contrato

Notação: `canon(x)` = JSON UTF-8 com `sort_keys=True`, `ensure_ascii=False`, `separators=(",",":")`, `allow_nan=False`. Assinatura = Ed25519 sobre `canon(objeto sem o campo signature)`, em hex minúsculo. Toda mensagem com `protocol_version=1`, `alg`, `kid`.

### 3.1 M1 — Certificado de revisão independente

```json
{"protocol_version":1,"alg":"Ed25519","kid":"iss-2026-11",
 "review_type":"independent_human","draft_sha256":"<hex>",
 "decision":"APROVADO","reviewer_id":"...",
 "review_record_url":"https://...","evidence_refs":["https://..."],
 "issued_at":1713900000,"expires_at":1713907200,"signature":"<hex>"}
```

Verificação: `K_ISS_PUB[kid]`; `draft_sha256` recalculado por `draft_digest(E1)` (§5); `issued_at ≤ now < expires_at`, TTL ≤ 86400s; `decision` exatamente `APROVADO`; `review_type` exatamente `independent_human`; `reviewer_id` ≠ aprovador do Gate. A chave pública **não** consegue assinar — isto resolve C1.

### 3.2 M2 — Envelope do registro confiável

```json
{"protocol_version":1,"alg":"Ed25519","kid":"reg-2026-11",
 "record":{"reviewer_id":"...","review_record_url":"https://...",
   "draft_sha256":"<hex>","decision":"APROVADO","status":"FINAL",
   "independent":true,"revoked":false,"evidence_refs":["https://..."],
   "issued_at":1713900000,"expires_at":1713903600,"registry_seq":91827},
 "served_at":1713900005,
 "signature":"<hex>"}
```

Correção C2: a assinatura cobre **todos** os campos acima exceto `signature`, inclusive `served_at`, `registry_seq`, `protocol_version`, `alg` e `kid`. Qualquer alteração em metadados invalida a assinatura.

Correção O3/2.1-1: `registry_seq` é **autoritativo no servidor do registro**, monotônico por `review_record_url`, emitido no envelope; o broker mantém a autoridade local de *aceite* em armazenamento persistente:

```
conexo_registry_sequences(review_record_url PK, max_seq_accepted, updated_at)
```

A atualização é atômica por comparação e troca (`CAS`): o broker lê `max_seq_accepted`, valida assinatura, TTL, frescura e sequência, e só então faz `UPDATE ... WHERE max_seq_accepted = valor_lido`; se outra requisição tiver avançado a linha, a transação falha e o envelope é recusado. `seq <= max_seq_accepted` → `review_record_replay_detected`, mesmo com assinatura válida e `served_at` dentro da janela. A sequência **só avança após aceite completo**, nunca em falha; um envelope idêntico reapresentado é replay e não gera nova escrita. Memória local do cliente pode ser *sinal* de suspeita, mas **nunca** é requisito de segurança nem fonte de verdade; `registry_seq_floor` foi removido do contrato. Reinício do broker não pode zerar a memória — `SEC-36` prova persistência.

Validação: assinatura, TTL do `record` ≤ 3600s, `served_at` conforme §6.1, `registry_seq` monotônico no servidor, `revoked is False`, `status=="FINAL"`, `independent is True`, igualdade de `draft_sha256`, `reviewer_id`, `evidence_refs` e `review_record_url` com M1.

### 3.3 M3 — Liberação do responsável (Gate RC10.5)

```json
{"schema":"conexo-owner-release/1","protocol_version":1,"alg":"Ed25519",
 "kid":"gate-2026-11","issued_at":1713900008,"expires_at":1713903608,
 "payload":{ ... campos atuais do owner-release ... },
 "signature":"<hex>"}
```

Campos assinados: todos os acima, exceto `signature`. O broker verifica com `K_GATE_PUB[kid]` e exige: `payload.owner_id == 3`, `payload.review_mode == "owner"`, 13 checks `VERIFICADO` com evidência não vazia, `version_sha256` de 64 hex igual ao do pacote, `payload.wordpress.post_id` igual ao post lido, `content_sha256` equivalente a `content_digest(raw)` (§5), TTL ≤ 3600s.

**Estado real:** o Gate RC10.5 atual entrega `conexo-owner-release/1` por GET autenticado, sem assinatura Ed25519 própria verificável offline. Enquanto essa assinatura não existir, **nenhum publish/schedule pelo broker é autorizado**; o bloqueio permanece. A implementação de `kid` no Gate é pré-condição da Fase D.

Rotação: novo par de chaves publicado com `kid` novo; broker aceita `kid` antigo por no máximo 24h; após isso, `kid` antigo entra em lista de revogação e é recusado. Rotação de emergência invalida `kid` imediatamente e exige reemissão de M3. `K_GATE` privada nunca sai do Vault.

### 3.4 M4 — Correlação WordPress (correção A1)

Três leituras distintas, com papéis diferentes:

| Endpoint | Nome | Autenticação | Campos exigidos | Papel |
|---|---|---|---|---|
| `GET /wp-json/wp/v2/posts/{id}?context=edit` | **E1** | sim | `id`, `status`, `modified`, `slug`, `categories`, `featured_media`, `title.raw`, `content.raw`, `link`, `meta._conexo_mkt_rss_run_id`, `meta._conexo_editorial_operation_nonce` | **única** fonte de versão; base de `draft_digest` e `content_digest`; na recuperação, o nonce é lido **autenticamente** aqui |
| `GET /wp-json/wp/v2/posts/{id}?context=view` | **E2** | sim | `id`, `status`, `modified`, `slug`, `link`, `content.rendered` | checar que a representação REST pública corresponde ao mesmo objeto |
| `GET /{slug}/?conexo_verify=<versão>` | **E3** | não | HTTP 200, `<title>`, `meta description`, `link rel=canonical`, iframe/`VideoObject` quando aplicável | conferir SEO público; **não** fornece `id`, `modified` ou `status` |

Correlação obrigatória: E1 e E2 com mesmo `id`, mesmo `modified`, mesmo `status`, mesmo `slug`; `meta._conexo_mkt_rss_run_id` igual quando presente nos dois. **Recuperação pós-falha (2.1-5):** o broker precisa ler `meta._conexo_editorial_operation_nonce` de E1 com a mesma identidade autenticada; ausência ou divergência desse meta **não** autoriza declarar `FAILED` — o caso permanece `UNKNOWN`/`transport_unknown_inspect` (`SEC-37`). Antes da escrita o meta pode não existir; depois dela, a confirmação da escrita depende dele. E1↔E3 por `slug` + canonical exato + título/descrição esperados (padrão já usado em `tools/publish_owner_approved.py::verify_public_seo`). String achatada de conector nunca é promovida a `raw`. Divergências: `wordpress_context_*_mismatch` / `wordpress_content_raw_unavailable`.

### 3.5 M5 — Recibo do broker (pós-escrita)

Emitido somente após resultado conhecido da escrita (correção 2.1-6). O campo `status` tem **exatamente** quatro valores:

| `status` | Significado | Nova escrita? |
|---|---|---|
| `published` | publicação efetivamente confirmada por E1/E2/E3 | sim, 1 |
| `scheduled` | agendamento efetivamente confirmado (`future`, `post_date_gmt` preservada) | sim, 1 |
| `idempotent` | operação anterior recuperada, sem nova escrita | não |
| `transport_unknown_inspect` | resultado ainda não comprovado; exige inspeção humana | não (automática) |

```json
{"status":"published|scheduled|idempotent|transport_unknown_inspect",
 "post_id":0,"nonce":"<hex>","retry_automatic":false,
 "operation_nonce":"<hex>","intent":"publish|schedule"}
```

`verified` **não é um status de publicação**: é, no máximo, um sinal interno de que as verificações M1–M4 passaram. Campo `verified` não deve aparecer no recibo como prova de publicação. `retry_automatic` é sempre `false` quando o resultado é incerto. Nenhum recibo contém selo novo de aprovação nem autoriza publicação posterior.

## 4. Ordem de verificação no broker

Pré-condições (antes de qualquer `POST` editorial):

1. Perfil e allowlist de origem (§2.3); identidade de serviço; modo `wp_broker` explícito; intent ∈ {`publish`, `schedule`}.
2. Pacote canônico: `stage == "ready"`, `version_sha256` 64 hex, `payload.wordpress.post_id` int > 0.
3. Turso: `require_release_trace` com `run_id` válido, relido antes da escrita.
4. M4: E1/E2/E3 correlacionados (§3.4); `content.raw` íntegro; sincronização de relógio verificada (§6.1).
5. M1: assinatura, TTL, identidade e `draft_digest(E1)`.
6. M2: assinatura do envelope inteiro, frescura, sequência autoritativa, revogação, igualdade com M1.
7. M3: assinatura do Gate, `kid`, TTL, owner 3, 13 checks, vínculo de post/versão.
8. Ponte de digests (§5): `draft_digest(E1)` com M1/M2; `content_digest(E1.raw)` com M3; `E1.raw == package.payload.content` byte a byte.
9. Escrita única com `operation_nonce` reservado atomicamente (§6). Só depois disso M5.

Nenhuma etapa autoriza a seguinte por omissão; falha é terminal, sem escrita.

## 5. Definição formal dos digests (correção C4)

| Nome | Implementação | Entrada | Normalização | Uso |
|---|---|---|---|---|
| `draft_digest(post)` | `editorial_factual_certificate.draft_digest` | objeto REST **E1** | campos `id`, `status`, `title`, `content` (objeto → `raw`), `slug`, `categories` **ordenados**, `featured_media`; `canon()` | comparar **somente** com `draft_sha256` de M1 e M2 |
| `content_digest(body)` | `mkt_flow_p0.gate_unified.content_digest` | string UTF-8 de `E1.content.raw` | bytes exatos da string, sem HTML renderizado | comparar **somente** com `content_sha256` de M3 |
| `package_content_sha256` | SHA-256 de `package.payload.content` | string UTF-8 do pacote | bytes exatos | comparar com `E1.content.raw` byte a byte |
| `seo_sha256` | SHA-256 de `canon(seo)` | `provider`, `canonical`, `title`, `description` | `canon()` | uso exclusivo do Gate de SEO no broker |

`draft_digest` e `content_digest` **têm entradas e normalizações diferentes e não podem ser comparados entre si**. A ponte segura é:

```
E1.content.raw == package.payload.content              (byte a byte)
draft_digest(E1) == M1.draft_sha256 == M2.record.draft_sha256
content_digest(E1.content.raw) == M3.content_sha256
```

Nenhum valor é reutilizado fora da sua coluna. Teste obrigatório: alterar um único byte de `raw` invalida as três verificações, sem escrita.

## 6. Nonce, concorrência e tempo

### 6.1 Tempo (correção O5)

O broker mede o desvio de relógio na mesma requisição usando o cabeçalho `Date` de E1 (WordPress) e do serviço de registro:

- `skew = max(|hora_do_servidor - hora_local|)`;
- se `skew > 30s` ou algum `Date` ausente/inválido → `CLOCK_SYNC_UNVERIFIED`, sem escrita;
- janela aceita para `served_at`: `[now - (120s + skew), now + (30s + skew)]`;
- `issued_at/expires_at` são sempre comparados com `now` local **após** a checagem de skew;
- testes fixam relógio (`now`) e simulam skew de 60s e cabeçalho ausente (`SEC-34`, `SEC-35`).

### 6.2 Reserva, nonce e reconciliação (correções A3/O4/2.1-2/2.1-3/2.1-4)

**Atomicidade distribuída não é afirmada.** Uma transação no banco do broker não torna atômica uma chamada HTTP ao WordPress. A garantia de "no máximo uma escrita" vem de três mecanismos, nesta ordem:

1. **Reserva persistente local** — `conexo_editorial_operations(nonce PK, post_id, version_sha256, body_sha256, state, created_at, updated_at)`, com chave única em `(post_id, nonce)` **e** restrição única em `(post_id, version_sha256)` para os estados ativos `RESERVED`, `IN_FLIGHT`, `WRITTEN` (2.1-3). A reserva usa `INSERT ... ON CONFLICT DO NOTHING` em transação com bloqueio de linha; conflito de versão ativa → `VERSION_ALREADY_IN_FLIGHT`/`VERSION_ALREADY_CONSUMED`, sem POST. Linhas `FAILED` podem ser removidas para permitir nova tentativa com outro nonce.
2. **Idempotência no endpoint WordPress** — o broker envia `operation_nonce` e `version_sha256` na chamada ao Gate/broker; o WordPress persiste esse nonce como `meta._conexo_editorial_operation_nonce` e como chave única em sua própria tabela, recusando uma segunda escrita da mesma versão. O servidor, não o cliente, é a autoridade final da idempotência.
3. **Reconciliação autenticada** — após timeout ou erro entre POST e recibo, o broker relê E1 (§3.4), incluindo `meta._conexo_editorial_operation_nonce`, e compara `post_id`, versão e nonce.

Estados: `RESERVED` → `IN_FLIGHT` (gravado **antes** do POST) → `WRITTEN` | `FAILED` | `UNKNOWN`. `IN_FLIGHT` é a marca explícita de que uma chamada externa pode ter ocorrido; por isso **nenhum timeout, sozinho, autoriza `FAILED`**.

Três classes de repetição:

| Classe | Entrada | Resultado |
|---|---|---|
| Repetição segura | mesmo nonce, mesmo `body_sha256`, `WRITTEN` | devolver M5 `idempotent` anterior; **nenhuma** segunda escrita |
| Repetição conflitante | mesmo nonce, `body_sha256` diferente | `NONCE_BODY_CONFLICT`; nenhuma escrita |
| Versão já ativa/consumida | nonce novo, `(post_id, version_sha256)` já em estado ativo | `VERSION_ALREADY_IN_FLIGHT`/`VERSION_ALREADY_CONSUMED`; nenhuma escrita |

Reconciliação (2.1-4):

- **Presença confirmada** — E1 autenticado traz o mesmo `operation_nonce`, `post_id` e versão → `WRITTEN`, M5 `published`/`scheduled` ou `idempotent` conforme a operação original; 0 nova escrita.
- **Ausência confirmada** — E1 autenticado responde de forma inequívoca que não existe post com aquele nonce **e** o WordPress confirma que a transação não foi aplicada (consulta ao registro de idempotência do servidor) → `FAILED`; novo nonce pode ser usado, com nova validação M1–M4.
- **Resultado desconhecido** — timeout, HTTP 5xx, JSON inválido, meta ausente/divergente ou resposta contraditória → `UNKNOWN`, M5 `transport_unknown_inspect`, `retry_automatic: false`, nenhuma escrita automática. **Não** é `FAILED`.

TTL de 48h para limpeza de registros antigos, mantendo o hash do corpo e o `registry_seq` por mais tempo para detectar replay tardio. Testes `SEC-30`–`SEC-33`, `SEC-37` e `SEC-38` cobrem concorrência, queda e distinção de ausência.

## 7. Testes

Convenção: testes OFFLINE usam HTTP mockado, relógio fixo e espião de `requests.post`; **nenhum deles publica de verdade**. Todo teste negativo afirma `requests.post` chamado zero vezes.

### 7.1 Negativos da Fase B — SEC-01…SEC-29 e SEC-36 (bloqueio intacto)

| ID | Cenário | Bloqueio esperado |
|---|---|---|
| SEC-01 | sem M1 | `trusted_factual_review_missing` |
| SEC-02 | M1 assinado com chave privada errada | `certificate_invalid` |
| SEC-03 | M1 expirado | `certificate_invalid` |
| SEC-04 | `decision = REJEITADO` | `certificate_invalid` |
| SEC-05 | `review_type != independent_human` | `certificate_invalid` |
| SEC-06 | `draft_sha256` de outro draft | `certificate_invalid` |
| SEC-07 | envelope M2 sem assinatura | `review_record_signature_missing` |
| SEC-08 | 1 byte alterado em `record` | `review_record_signature_invalid` |
| SEC-09 | `served_at` alterado fora da assinatura | `review_record_signature_invalid` |
| SEC-10 | `registry_seq` alterado fora da assinatura | `review_record_signature_invalid` |
| SEC-11 | envelope assinado com `K_ISS` em vez de `K_REG` | `review_record_signature_invalid` |
| SEC-12 | `served_at = now-300s` | `review_record_stale_response` |
| SEC-13 | `served_at = now+60s` | `review_record_stale_response` |
| SEC-14 | `registry_seq` regressivo em envelope assinado e dentro da janela | `review_record_replay_detected` |
| SEC-36 | envelope com `registry_seq` já aceito reapresentado após **reinício do broker** | `review_record_replay_detected` (persistência em `conexo_registry_sequences`) |
| SEC-15 | `revoked = true` (assinado) | `review_record_mismatch` |
| SEC-16 | `status = PENDING` | `review_record_mismatch` |
| SEC-17 | `independent = false` | `review_record_mismatch` |
| SEC-18 | M2 sem `expires_at` | `review_record_evidence_missing` |
| SEC-19 | E1/E2 com `modified` diferentes | `wordpress_context_version_mismatch` |
| SEC-20 | conteúdo achatado como `raw` | `wordpress_content_raw_unavailable` |
| SEC-21 | M3 ausente | `gate_owner_release_missing` |
| SEC-22 | M3 de outro post | `gate_owner_release_post_mismatch` |
| SEC-23 | conteúdo alterado após aceite | `remote_version_mismatch` |
| SEC-24 | `owner_id = 4` | `gate_owner_release_invalid` |
| SEC-25 | check do M3 sem evidência | `gate_owner_release_invalid` |
| SEC-26 | HTTP 200 com pacote inválido | recusa semântica, sem POST |
| SEC-27 | timeout do registro | `trusted_review_unavailable`, sem POST |
| SEC-28 | falha de rede no readback E1 | `WP_READ_OUTCOME_UNKNOWN`, sem POST |
| SEC-29 | perfil `staging` com origem `https://conexotech.com.br` | `BROKER_ORIGIN_NOT_ALLOWED`, sem POST |

`BLOCK-TEMP-01` (correção A4): teste **temporário**, existente hoje e em `tests/test_editorial_broker_transport.py`, comprovando que `publish`/`schedule` com `wp_broker` recusam com `trusted_factual_review_broker_guard_not_integrated`. Não é teste do contrato implementado: deve ser removido **no mesmo commit** que implementar M1–M4 no broker e substituído pelos testes `CONTRACT-01…` com aprovação válida. Mantê-lo após a implementação seria circular; removê-lo antes seria abrir o caminho sem prova.

### 7.2 Positivos identificados (correção O1)

| ID | Entrada | Pré-condição | Resultado esperado |
|---|---|---|---|
| POS-01 | M1+M2+M3 válidos, E1/E2/E3 correlacionados, `intent=publish`, nonce N1 | perfil `staging`, relógio sincronizado, Turso relido | 1 POST no broker, `status=published`, `retry_automatic=false` |
| POS-02 | idem, `intent=schedule`, `post_date_gmt` futura | mesmo de POS-01 | 1 POST, `status=scheduled`, data preservada no WP |
| POS-03 | repetição de POS-01 com mesmo nonce e mesmo corpo | `state=WRITTEN` | `status=idempotent`, **0** POST adicional |
| POS-04 | repetição de POS-01 com mesmo nonce e corpo diferente | `state=WRITTEN` | `NONCE_BODY_CONFLICT`, 0 POST |
| POS-05 | simulação de queda após POST antes do recibo | nonce persistido, E1 autenticado com `meta._conexo_editorial_operation_nonce` | recuperação por E1, `status=published`/`idempotent`, sem segundo POST, evidência de restauração |

### 7.3 Negativos adicionais de concorrência/tempo (Fase C)

| ID | Cenário | Esperado |
|---|---|---|
| SEC-30 | dois pedidos concorrentes com o mesmo nonce | 1 escrita, 1 `idempotent` |
| SEC-31 | nonce reutilizado com `version_sha256` distinta | `VERSION_ALREADY_CONSUMED` |
| SEC-37 | queda após POST; E1 sem `meta._conexo_editorial_operation_nonce` ou com nonce divergente | `UNKNOWN` → M5 `transport_unknown_inspect`; **nunca** `FAILED` |
| SEC-32a | queda após POST; E1 e registro de idempotência do WP confirmam **ausência** da escrita | `FAILED`, sem retry automático; novo nonce permitido após nova validação |
| SEC-32b | queda após POST; leitura inconclusiva (timeout/5xx/JSON inválido) | `UNKNOWN` → `transport_unknown_inspect`; sem retry automático |
| SEC-38 | duas operações concorrentes com o mesmo `(post_id, version_sha256)` | 1 reserva, a outra `VERSION_ALREADY_IN_FLIGHT`; 1 POST no máximo |
| SEC-33 | `kid` de M3 revogado | `gate_owner_release_invalid` |
| SEC-34 | skew de 60s | `CLOCK_SYNC_UNVERIFIED` |
| SEC-35 | cabeçalho `Date` ausente | `CLOCK_SYNC_UNVERIFIED` |

`CONTRACT-01…` (Fase C, somente após implementação): versão válida com todos os campos assinados deve autorizar exatamente um POST; estes testes **não** substituem `BLOCK-TEMP-01` até que a Fase E seja cumprida.

## 8. Classes de evidência (correção O6)

| Classe | Ambiente | Ferramenta | Evidência exigida | Não serve como prova de |
|---|---|---|---|---|
| OFFLINE | checkout preparado, HTTP mockado, relógio fixo | pytest | log com contagem, SHA do commit, `git status` limpo | publicação real, integração server-side |
| HOMOLOGAÇÃO REAL | WordPress de homologação, banco isolado, domínio da allowlist | cliente + broker reais | GETs E1/E2/E3 autenticados (com hash), POST único, `post_id`/status conferidos, sem segredos em logs | produção |
| RESTAURAÇÃO | backup datado restaurado em banco separado | ferramenta de backup verificável | manifesto SHA-256, data/tamanho, saída do restore, contagem de posts/temas/plugins antes/depois, confronto com produção | sucesso de publicação |
| DECISÃO | revisão do proprietário | registro único | aceite explícito vinculado ao SHA | automação por suíte verde |

Evidência de OFFLINE nunca é apresentada como homologação; evidência de homologação nunca é apresentada como restauração; nenhuma substitui aceite humano.

## 9. Critérios de aceitação para retirar o bloqueio

1. `SEC-01`…`SEC-38` (incluindo `SEC-32a`/`SEC-32b`) verdes no checkout preparado; SHA e contagem registrados.
2. 5 positivos (`POS-01`…`POS-05`) verdes, com 1 POST no máximo por versão e status M5 inequívoco.
3. Homologação real com E1/E2/E3 lidos e correlacionados; logs e hashes no Registro Único.
4. Restauração comprovada em ambiente isolado (manifesto datado + saída do restore + contagens confrontadas).
5. M1/M2/M3 com assinatura assimétrica e `kid`; nenhum cliente com chave privada; HMAC legado só no servidor.
6. Reserva persistente com `IN_FLIGHT`, restrição única `(post_id, version_sha256)` e reconciliação provadas; nenhuma alegação de atomicidade distribuída.
7. Skew medido e janelas aplicadas; nenhum teste com relógio assumido correto; `registry_seq` persistido no broker sobrevive a reinício.
8. Revisão humana do proprietário, vinculada à versão exata; PR #130 sem merge/deploy automático; seção própria no Registro Único.

## 10. Ordem de trabalho autorizável

1. Aprovação desta revisão documental (Fase A). Nada foi implementado.
2. Fase B: implementar `SEC-01`…`SEC-29` e `SEC-36` em branch isolada, **sem alterar o bloqueio**; rodar suíte OFFLINE e registrar SHA.
3. Validar criptografia (§3.1–§3.3) e semântica de digests (§5) por revisão assistida e por teste vetorial com entradas fixas.
4. Fase C: implementar M1–M4 no broker, reserva/`IN_FLIGHT`, nonce no WordPress, restrição única de versão, `kid`/rotação e `SEC-30`…`SEC-38`; `BLOCK-TEMP-01` só sai no commit que prova `CONTRACT-01…`.
5. Fase D: homologação real com origem isolada e restauração comprovada.
6. Fase E: decisão de integração com os 8 critérios — até lá, PR #130 permanece draft.

## 11. Riscos em aberto

- Registro assinado com `registry_seq` autoritativo e rotação ainda não provisionado.
- Gate RC10.5 ainda não emite M3 assinado com `kid`.
- Domínio de homologação (`<HOMOLOGATION_HOST>`) precisa ser definido pelo proprietário.
- Skew real entre Hostinger, WordPress e registro precisa ser medido, não assumido.
- Latência de 4 leituras + verificação por publicação precisa ser aceita explicitamente.
- Segredos nunca devem aparecer em logs, testes ou Registro Único.

## 12. Definição de pronto da revisão documental

- [x] C1–C4 e A1–A4 respondidos;
- [x] cinco positivos identificados com entrada, pré-condição e resultado;
- [x] M3 com formato, campos assinados, verificação e rotação;
- [x] sequência autoritativa no servidor e maior `registry_seq` aceito persistido no broker;
- [x] reserva persistente, `IN_FLIGHT`, idempotência no WordPress e reconciliação sem atomicidade distribuída;
- [x] restrição única `(post_id, version_sha256)`;
- [x] ausência confirmada distinta de resultado desconhecido;
- [x] meta de nonce do E1 na leitura autenticada de recuperação;
- [x] M5 com estados `published`/`scheduled`/`idempotent`/`transport_unknown_inspect`;
- [x] janelas temporais com medição de skew;
- [x] OFFLINE × homologação × restauração separados.

Aprovação desta revisão **não** autoriza Fase B automaticamente; o proprietário deve autorizar cada fase.
