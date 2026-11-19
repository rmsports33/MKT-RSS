# Auditoria — Revisor Único e Gate no checkout `d50344d` (19/11/2026)

Escopo: leitura do código em `d50344db52ad82acfc9b043fd0a790883ce780c5` (mesmo conteúdo do clone
`~/mkt-rss-runtime-prepared-20261119`), sem escrita em produção, sem rede e sem alterar código.
Este documento não aprova publicação nem altera o Gate.

## 1. Pontos de entrada

### 1.1 Revisor Único

| Ponto de entrada | Arquivo | Papel |
|---|---|---|
| `verify_independent_review(post, certificate, signing_key, lookup_review, *, now=None)` | `editorial_trusted_review.py:10` | única função do módulo; consulta registro confiável injetado e compara identidade, digest, decisão, status, independência, evidências e revogação |
| `editorial_factual_certificate.verify_factual_certificate` / `draft_digest` | `editorial_factual_certificate.py` | assinatura HMAC do certificado e digest do rascunho, usados por `verify_independent_review` |

Não existe implementação de `lookup_review` no repositório: a consulta ao registro de revisão é
sempre injetada pelo chamador (confirmado por busca textual — só aparece em `editorial_trusted_review.py`
e na documentação).

### 1.2 Gate editorial (lado Python consumidor)

| Ponto de entrada | Arquivo | Papel |
|---|---|---|
| `authorize_publish(post, factual_review=None, *, package=None, core_root=None, expected_category_id=10, owner_release=None)` | `editorial_publish_gate.py:64` | guard local fail-closed: prontidão do post, proveniência do corpo bruto, recibo do proprietário e pacote canônico |
| `require_publish_authorization(...)` | `editorial_publish_gate.py:128` | mesma regra, mas levanta `PermissionError` com os bloqueios |
| `inspect_wordpress_draft(fetch_post, post_id, factual_review, *, expected_category_id=10, fetch_post_view=None)` | `editorial_wordpress_adapter.py:231` | lê o post (edit+view), monta readback e roda o guard |
| `assemble_wordpress_context_readback(edit_post, view_post)` | `editorial_wordpress_adapter.py:130` | pareia `context=edit` (raw) e `context=view` (rendered) do mesmo post/versão/status |
| `validate_wordpress_content_readback(post)` | `editorial_wordpress_adapter.py:182` | exige `content.raw` real, valida proveniência e confere marcação de vídeo no rendered |
| `validate_owner_release(packet, post_id=None)` | `mkt_flow_p0/gate_unified.py:198` | valida `conexo-owner-release/1`, proprietário 3, `review_mode=owner`, 13 checks e vínculo ao post |
| `read_owner_release(post_id, *, session, auth, ...)` | `mkt_flow_p0/gate_unified.py:233` | lê o recibo **do servidor** (`/wp-json/conexo/v1/editorial/owner-release/{id}`) e o valida |
| `advisory_gate_receipt(info, *, markdown=None, date=None)` | `mkt_flow_p0/gate_unified.py:116` | comprovante advisory derivado do aceite real; nunca autoriza |
| `build_release_trace(packet, *, run_id=None)` | `mkt_flow_p0/gate_unified.py:281` | trilha dos 10 estágios; `publication_authorized` sempre `False` |
| `publish_via_broker(...)` | `mkt_flow_p0/editorial_broker_transport.py:71` | único caminho de publicação; exige pacote idêntico ao servido pelo Gate |
| `tools/publish_owner_approved.py::release` (CLI `--post-id --version --execute`) | `tools/publish_owner_approved.py:77` | libera publicação a partir do recibo do servidor |
| `tools/schedule_owner_approved_wordpress.py` | `tools/` | agenda post futuro com o mesmo recibo |
| `pipeline_rss.py:469-470` | `pipeline_rss.py` | chama `authorize_publish` no fluxo RSS |

O plugin PHP do Gate (`conexo-editorial-gate`) **não** está neste repositório; aqui há apenas os
consumidores e validadores do pacote emitido por ele.

## 2. Contratos verificados no código

| Contrato | Onde | Situação |
|---|---|---|
| Só `content.raw` comprova versão; string achatada e `rendered` nunca valem como fonte | `editorial_publish_gate.py:13-28`, `editorial_wordpress_adapter.py:115-127` | implementado |
| Readback exige mesmo `id`, mesmo `modified` e mesmo `status` entre edit e view | `editorial_wordpress_adapter.py:140-156` | implementado |
| `_conexo_mkt_rss_run_id` divergente entre contextos bloqueia | `editorial_wordpress_adapter.py:161-168` | implementado |
| Marca de proveniência `cxeg-package:v1` validada no corpo bruto | `editorial_publish_gate.py:71-77` | implementado |
| Recibo do proprietário: `owner_id == 3`, `review_mode == "owner"`, `version_sha256` SHA-256, `checks` com 13 itens e evidência real | `gate_unified.py:198-230` | implementado |
| Versão aprovada vem do servidor; hash colado é só conferência | `gate_unified.py:233-264`, `tools/publish_owner_approved.py:87-94` | implementado |
| Bloqueio por post divergente e por conteúdo divergente | `editorial_publish_gate.py:91-95` | implementado |
| Publicação exige pacote canônico e `core_root` válidos | `editorial_publish_gate.py:96-114` | implementado |
| Broker exige pacote **idêntico** ao servido e política por intenção (publish/schedule) | `editorial_broker_transport.py:71-93` | implementado |
| HTTP 200 não é validação semântica | `gate_unified.py:254-262` | implementado e testado |
| Revisor confiável nunca autoriza publicação sozinho | `editorial_trusted_review.py` + testes | documentado e testado |

## 3. Achados

### A1 — O Revisor Único não está ligado ao caminho de publicação (alto)

`verify_independent_review` não é chamado por `authorize_publish`, pelo broker, pelo pipeline nem
pelos CLIs. Busca textual no checkout: as únicas ocorrências são a definição, dois testes e um
documento. Na prática, o parecer do revisor não é consultado em nenhuma decisão de publicação: o
Gate só verifica o recibo do proprietário e o pacote canônico.

### A2 — `factual_review` é aceito e ignorado (alto)

Em `authorize_publish`, o parâmetro `factual_review` só influencia o resultado quando
`package`/`core_root` estão ausentes (`editorial_publish_gate.py:96-100`), adicionando
`trusted_factual_review_missing`. Quando o pacote canônico existe, um `factual_review`
falso, vazio ou ausente não é checado. O teste `tests/test_readback_gate_parecer_e2e.py:135-147`
inclusive passa `{"verified": True}` sem que isso seja validado — o teste fixa o comportamento atual.

### A3 — Bloqueio `trusted_factual_review_missing` depende do pacote, não da revisão (médio)

O código de bloqueio sugere ausência de revisão factual confiável, mas é emitido apenas quando o
pacote canônico falta. Isso pode mascarar A2 em logs e em pareceres: um pacote presente silencia o
bloqueio sem que qualquer revisor tenha sido consultado.

### A4 — Nenhum teste cobre revisor reprovado bloqueando publicação com pacote válido (médio)

Cobertura existente: 6 testes do módulo de revisor (registro correto, sem store, revogado, conteúdo
alterado, revisor divergente, erro de store) e 6 testes ponta a ponta de readback+Gate. Nenhum
teste monta pacote canônico válido + recibo válido + parecer **reprovado** para provar bloqueio,
porque esse caminho não existe hoje.

### A5 — Caminho de transição sempre nega, por desenho (baixo)

`editorial_publish_transition.plan_publish_transition` chama `authorize_publish` e devolve
`allowed: False` em qualquer caso (`editorial_publish_transition.py:13-23`). É fail-closed, mas
duplica a regra e não pode ser usado: risco de confusão sobre qual guard é o oficial.

### A6 — Dois nomes para a mesma checagem de conteúdo (baixo)

`content_digest` (gate_unified) e o hash inline em `validate_wordpress_content_readback`
(`editorial_wordpress_adapter.py:226`) calculam SHA-256 do corpo bruto separadamente. Hoje
coincidem, mas são duas implementações a manter.

## 4. Testes existentes (mapa)

| Arquivo | Foco | Provas |
|---|---|---|
| `tests/test_editorial_trusted_review.py` | Revisor Único | 6 negações/aceitação do registro confiável |
| `tests/test_readback_gate_parecer_e2e.py` | ponta a ponta simulado | readback nativo, parecer, recibo e Gate na mesma versão; recusa por conteúdo e por post; HTTP 200 inválido; recibo advisory |
| `tests/test_gate_unified.py` | contratos do Gate | 24 testes: 13 checks, mapa check→estágio, recibo do servidor, HTTP rejeitado, ausência de credenciais, trilha sem autorização, índice de pendências, D1 |
| `tests/test_gate_local_unification.py` | guard local | 10 testes: sem recibo, recibo inválido, post divergente, conteúdo editado, bloqueios não repetidos, comprovante advisory |
| `tests/test_editorial_publish_gate.py` | guard | 17 testes: pacote obrigatório, mídia, status, proveniência, raw vs rendered, snapshot canônico |
| `tests/test_editorial_wordpress_adapter.py` | readback | 22 testes: edit/view, id/modified/status, string achatada, raw ausente, vídeo, mutação, JSON-LD |

Suíte completa no checkout preparado: 1619 passed, 11 skipped, 0 failed.

## 5. Recomendações (não executadas)

1. Ligar o Revisor Único ao `authorize_publish`: exigir parecer verificado **ou** declarar
   explicitamente que o caminho owner dispensa revisor, sem emitir código ambíguo (A1, A3).
2. Validar `factual_review` quando o pacote canônico existir, ou remover o parâmetro para não
   sugerir uma checagem inexistente (A2).
3. Criar teste de pacote+recibo válidos com parecer reprovado, provando bloqueio (A4).
4. Reduzir `plan_publish_transition` a um único guard oficial ou removê-lo (A5).
5. Reutilizar `content_digest` no readback (A6).

Nenhum desses itens foi implementado nesta auditoria.
