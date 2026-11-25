# EVIDÊNCIA — FASE A (PREFLIGHT SOMENTE LEITURA)

**Data:** 25/11/2026
**Escopo:** verificação antes de qualquer publicação. NENHUMA escrita, NENHUMA aprovação, NENHUMA publicação.
**Resultado:** PREFLIGHT PARCIAL — dois bloqueios concretos impedem a Fase B.

---

## A1 — Integridade do código

| Item | Valor | Situação |
|------|-------|----------|
| Branch | `feat/mkt-gate-v1-certified-publish-20261125` | ✅ |
| SHA local | `505702d6120b9acbe5255f4a14c67ced14f3d5b9` | ✅ |
| SHA remoto | `505702d6120b9acbe5255f4a14c67ced14f3d5b9` | ✅ igual |
| Plugin CAS local | `conexo-atomic-cas.php`, 8.539 bytes, 164 linhas | ✅ |
| Plugin CAS no servidor | 8.539 bytes, 164 linhas (readback MCP) | ✅ tamanho/linhas iguais |
| SHA-256 local do plugin | `828a5e999b662bf928c1e104bf441cf0a72445cef274b42bf3ae7b747a7b0897` | ✅ |

Nota: o cálculo de hash feito em JavaScript simplificado dentro do runtime diverge por causa de caracteres acentuados (UTF-8); não é uma divergência de arquivo. O tamanho e a contagem de linhas conferem exatamente.

## A2 — Rotas (sem autenticação, somente leitura/SANE)

| Verificação | Resultado |
|-------------|-----------|
| `OPTIONS /wp-json/conexo/v1/editorial/atomic-commit` | HTTP 200 (registrada) |
| `POST /wp-json/conexo/v1/editorial/atomic-commit` anônimo | HTTP 401 (protegida) |
| `GET /wp-json/conexo/v1/editorial/quality/9907` anônimo | HTTP 401 (protegida) |

## A3 — Rascunhos elegíveis (leitura autenticada, somente GET)

- `GET /wp-json/wp/v2/posts?status=draft` → HTTP 200
- Total de rascunhos: **149**
- Elegíveis para `draft_digest` (categoria 10, sem categoria 1, com imagem destacada): **78**
- Exemplo elegível: post **9900** (`anatel-manda-tim-desligar-funcao-que-bloqueia-telemarketing...`, categoria 10, featured_media 9912)
- Post 9907 (referência anterior): **na lixeira**, categoria 1, sem imagem — não elegível

## A4 — Parecer humano no Gate V1 (leitura autenticada, somente GET)

| Resultado | Detalhe |
|-----------|---------|
| **BLOQUEIO 1** | Nenhum dos 78 rascunhos elegíveis possui registro humano em `cxeg_quality_read`. Todos retornaram `HUMAN_REVIEW_RECORD_MISSING`. |
| Post 9907 | Sem registro; além disso está na lixeira. |

Consequência: não existe aprovação humana autenticada vinculada ao hash de nenhum rascunho elegível. Criar um parecer agora seria **duplicar/fabricar aprovação** — expressamente proibido. A Fase B não pode começar sem um parecer humano real, gerado pelo fluxo normal do Gate.

## A5/A6 — Certificado factual

Não emitido. Motivos:
1. Falta o parecer humano autenticado (A4).
2. A chave `CONEXO_EDITORIAL_GATE_KEY` não está disponível no executor (auditoria 18/11 a registra como ausente) e não há evidência de que esteja definida no servidor. Sem ela, o próprio plugin CAS responde 503.

## A7 — BUG CRÍTICO ENCONTRADO (BLOQUEIO 2)

O hash calculado pelo Python (`draft_digest`, usado no certificado) e o hash recalculado pelo plugin CAS (PHP) **não coincidiam**.

Teste local com post de exemplo (id 41, título `Notícia`, conteúdo `<p>Texto</p>`, slug `noticia`, categoria `[10]`, featured_media 12):

| Implementação | SHA-256 |
|---------------|---------|
| Python `draft_digest` | `1341bb92c336ebacfca6f3bd0284b3ff6744eab27519b072ef1b2ef9fa26becc` |
| Plugin CAS instalado (PHP) | `4a4b829b8bedf6f42515bf705d52f24b21a8e7f28152e2bf8483710362fa943e` ❌ |

Causa: Python usa `sort_keys=True` (ordem alfabética das chaves) e ordena as categorias; o PHP usava ordem de inserção (`id, status, title, content, slug, categories, featured_media`) e não ordenava as categorias.

Impacto: **toda** tentativa de publicação falharia com 409 "Certificado factual inválido para esta versão", mesmo com parecer humano e chave válidos.

Correção **instalada em produção** (autorização do proprietário, 25/11/2026):
- Arquivo preservado no repositório: `docs/patches/conexo-atomic-cas-fixed.php`
- SHA-256: `c36db417ca1f1b0c6a11d6871e7481c915e526d3b83d3fbab7f3b63b1c4c91f3`
- 8.456 bytes, 170 linhas
- Nova função `cxeg_cas_digest()` com chaves em ordem alfabética e categorias ordenadas
- `php -l` aprovado
- Paridade local PHP ↔ Python confirmada: `1341bb92...` dos dois lados ✅
- Upload TUS: POST 201 + PATCH 204
- Readback autenticado: 8.456 bytes, 170 linhas, `cxeg_cas_digest` presente; hash do conteúdo retornado = `396add20...`, que é exatamente o SHA do arquivo local sem o `\n` final que o endpoint de leitura remove (confirmado localmente)
- Rotas após a instalação: `OPTIONS` = 200, `POST` anônimo = 401 ✅
- Arquivo anterior preservado em `C:\Users\LIVE2PC\AppData\Local\Temp\opencode\conexo-atomic-cas-BACKUP.php` (SHA `828a5e99...`)

---

## A8 — Chave do Gate (configurada, valor NÃO divulgado)

| Item | Registro |
|------|----------|
| Geração | Nova chave aleatória, 64 caracteres hex (32 bytes) |
| SHA-256 da chave (fingerprint, não é a chave) | `f2e293e5815e4f5e7d80d145c3199627a51d4f9b271fb4c5890ebc0f2622f58b` |
| Executor | `.env` local, chave `CONEXO_EDITORIAL_GATE_KEY` (arquivo ignorado pelo git) |
| Servidor | `wp-content/mu-plugins/conexo-gate-key.php`, 347 bytes, `define()` protegido por `if ( ! defined( ... ) )` |
| Upload | POST 201 + PATCH 204 |
| `php -l` | ✅ aprovado |
| Site após instalação | ✅ homepage 200; CAS OPTIONS 200; CAS POST anônimo 401 |
| Emissão/verificação de certificado no executor | ✅ emissão e auto-verificação OK com a chave real |
| Divulgação do segredo | ❌ Nenhuma — o valor não aparece neste documento, no chat nem em arquivo versionado |

Nota: o núcleo do Gate V1 já lia a chave via `defined()`/`getenv()` em três pontos; não havia `define()` no núcleo. O arquivo aditivo define a constante sem sobrescrever uma definição existente.

---

## Conclusão da Fase A

| Item | Situação |
|------|----------|
| Código versionado íntegro | ✅ |
| Plugin instalado íntegro (tamanho/linhas) | ✅ |
| Rotas registradas e protegidas | ✅ |
| Leitura autenticada funciona | ✅ |
| Parecer humano para publicar | ❌ inexistente |
| Chave do Gate no executor/servidor | ❌ não confirmada |
| Paridade de hash Python ↔ PHP | ✅ corrigida e instalada |
| Publicação | ❌ nenhuma |

**Fase B continua bloqueada.** Para prosseguir é preciso, nesta ordem:
1. ✅ Instalar a correção do plugin CAS — **feito e verificado**.
2. ✅ Configurar `CONEXO_EDITORIAL_GATE_KEY` no executor e no servidor — **feito e verificado**.
3. Gerar um parecer humano real no Gate V1 para um rascunho elegível, vinculado ao hash exato.
4. Somente então executar a Fase B com autorização específica.

O item 3 **não** foi feito nesta Fase A. Aguardando parecer humano real.
