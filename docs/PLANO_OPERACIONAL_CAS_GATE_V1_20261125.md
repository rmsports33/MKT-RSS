# PLANO OPERACIONAL — PUBLICACAO VIA CAS NO GATE V1

**Data:** 25/11/2026
**Status:** planejamento autorizado (passo 7). NENHUMA publicacao executada neste documento.
**Autorizacao operacional:** concedida pelo proprietario para o planejamento. A execucao de qualquer publicacao real exige autorizacao especifica adicional.

---

## 1. Objetivo

Definir a sequencia segura para usar a cadeia MKT-RSS -> Gate V1 -> WordPress em producao, com:
- certificado factual assinado
- aprovacao humana ja persistida no Gate (sem duplicacao)
- escrita atomica via CAS real
- readback e recibo verificaveis
- rollback comprovado

---

## 2. Estado atual (pre-operacional)

| Componente | Estado |
|------------|--------|
| Gate V1 RC10.4 | Ativo no site |
| `conexo-atomic-cas.php` | Instalado em `wp-content/mu-plugins/` (aditivo) |
| Rota `POST /wp-json/conexo/v1/editorial/atomic-commit` | Registrada; POST anonimo = 401 |
| Core do Gate | Inalterado |
| MKT-RSS `gate_review_reader.py` | 17 testes simulados |
| MKT-RSS `editorial_factual_certificate.py` | 18 testes |
| MKT-RSS `editorial_transport.py` | assessment obrigatorio, 6 testes |
| MKT-RSS `gate_certified_publish.py` | 8 testes, inclui backend CAS real simulado |
| Suíte consolidada | 48 testes aprovados |
| Publicacoes reais | NENHUMA |
| Conteudo alterado em producao | NENHUM |

---

## 3. Pre-requisitos antes de qualquer execucao real

| # | Pre-requisito | Como verificar |
|---|---------------|----------------|
| 1 | Backup completo recente (banco + arquivos) | UpdraftPlus: confirmar timestamp eIntegridade |
| 2 | Rollback testado em copia isolada | Restaurar backup em ambiente descartavel e conferir |
| 3 | Chave `CONEXO_EDITORIAL_GATE_KEY` presente no executor e no WP | Verificacao booleana, sem imprimir valor |
| 4 | Arquivos MKT-RSS commitados e SHA registrado | `git log -1` na branch isolada |
| 5 | Post de teste em draft, nao publico | `GET /wp-json/wp/v2/posts/{id}?context=edit` autenticado |
| 6 | Aprovacao humana existente para o hash exato | `GET /conexo/v1/editorial/quality/{id}` autenticado |
| 7 | Parecer de qualidade vigente | `valid_for_current_version: true` |
| 8 | Janela operacional combinada | Horario, responsavel, plano de comunicacao |
| 9 | Autorizacao especifica de publicacao | Registrada por escrito |

---

## 4. Sequencia operacional (a executar somente com autorizacao especifica)

### Fase A — Preflight (somente leitura)
1. Confirmar SHA do codigo MKT-RSS e do plugin CAS no WP
2. Verificar rotas: `quality/{id}` (GET) e `atomic-commit` (POST anonimo = 401)
3. Ler post de teste em draft e calcular `draft_digest`
4. Consultar registro humano autenticado via `gate_review_reader`
5. Emitir certificado factual com chave do executor
6. Auto-verificar certificado (sem publicar)
7. Registrar todos os hashes e SHAs em arquivo de evidencia

### Fase B — Publicacao atomica (uma vez, um post)
1. Gerar `operation_id` unico (UUID)
2. Chamar `certified_publish(...)` com backend CAS real
3. O Gate executa: transacao -> SELECT FOR UPDATE -> compara hash -> UPDATE -> COMMIT
4. Se qualquer verificacao falhar: ROLLBACK, nenhuma publicacao, operacao reservada para inspecao
5. Confirmar readback: status `publish`, hash igual ao esperado
6. Registrar recibo: `operation_id`, `expected_sha256`, `post_id`, `committed=true`

### Fase C — Pos-publicacao
1. Verificar pagina publica (GET anonimo)
2. Verificarse o conteudo publicado bate com o hash aprovado
3. Verificar recibo via `GET /conexo/v1/editorial/operation/{nonce}`
4. Registrar evidencias com timestamp, SHA e logs
5. Nao repetir a operacao

---

## 5. Rollback

### Se a escrita falhar antes do COMMIT
- Transacao ja revertida automaticamente pelo plugin CAS
- Operacao fica em `cxeg_cas_op_{operation_id}` com estado RESERVED
- Nao repetir sem inspecao

### Se a publicacao concluir mas divergir do conteudo aprovado
1. Suspender o executor MKT-RSS imediatamente
2. Restaurar o post de teste especifico a partir do snapshot autenticado (nao restaurar banco inteiro)
3. Confirmar readback apos restauracao
4. Registrar incidente e bloquear nova operacao ate diagnostico

### Se o plugin CAS causar erro no site
1. Remover apenas `wp-content/mu-plugins/conexo-atomic-cas.php` via gerenciador de arquivos
2. O core do Gate continua intacto e o site volta ao estado anterior
3. Confirmar homepage e wp-admin

**Nao restaurar banco inteiro como rollback de rotina.**

---

## 6. Criterios de aceite

| Criterio | Evidencia |
|----------|-----------|
| Certificado valido e vinculado ao hash | `draft_sha256` confere com `draft_digest(post)` |
| Aprovacao humana preservada | `valid_for_current_version: true` e `reviewer_id` valido |
| CAS executado | `committed: true` e `operation_id` unico |
| Readback autenticado | post `publish` com hash igual ao esperado |
| Recibo verificavel | `state: COMPLETE` na operacao |
| Sem duplicacao de aprovacao | Nenhuma nova aprovacao emitida pelo MKT-RSS |
| Sem escrita paralela | Somente uma rota de escrita utilizada |
| Producao controlada | Backup e rollback disponiveis |

---

## 7. Restricoes permanentes

- Nao publicar, agendar ou aprovar conteudo sem autorizacao especifica
- Nao executar testes destrutivos no site real
- Nao modificar o core do Gate
- Nao duplicar aprovacao humana
- Nao confundir `editorial_assessment` com aprovacao humana
- Nao usar o Gate V2 em producao
- Nao fazer merge, deploy ou push de codigo funcional sem autorizacao

---

## 8. Proxima acao minima

Aprovar formalmente este plano e escolher um post de teste em draft. Somente apos isso:
1. Fazer backup verificado
2. Executar Fase A
3. Registrar evidencias
4. Solicitar autorizacao especifica para Fase B

**Ate la, nenhuma publicacao sera executada.**
