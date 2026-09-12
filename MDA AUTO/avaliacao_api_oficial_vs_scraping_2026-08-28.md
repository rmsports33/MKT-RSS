# Avaliação — Integração com APIs oficiais dos marketplaces vs scraping

**Data:** 28/08/2026 — MKT Flow 3.7 → 3.8 (P1)
**Solicitado em:** "A final avalie a possibilidade de integrar a API oficial dos marketplaces para fazer scrapping"
**Decisão de arquitetura a respeitar:** pré-processamento externo determinístico; `ML-PUBLIC-API-STATUS` UNKNOWN até confirmação (cl. 4.3(c))

---

## 1. Resumo executivo

| Marketplace | Scraping HTML | API pública sem auth | API oficial afiliado (com auth) | Recomendação |
|---|---|---|---|---|
| **Mercado Livre** | **PROIBIDO** — cl. 4.3(c): "vedado uso de meio automatizado de scraping/extração de dados do site" (inclui busca via navegação/IA, confirmação confiança A) | **PENDENTE** — `https://api.mercadolibre.com/items/{id}` existe, mas termo não a excepciona claramente; hoje tratada como `ML-PUBLIC-API-STATUS: UNKNOWN` `policies/mercado_livre.json:47` | **PERMITIDA com confirmação** — existe *Mercado Livre Developers* (api.mercadolibre.com) com OAuth; afiliado deve confirmar por escrito se uso para preencher landing é compatível com cl. 4.3(c) | **Usar `MKTFLOW/ml_client.py:31` com cache TTL 300s + pedir confirmação escrita ao suporte afiliados antes de produção; nunca fazer scraping HTML** |
| **Shopee** | **PROIBIDO** — cl. 4.3(d) + `SH-AUTOMATED-EXTRACTION: FAIL` `policies/shopee.json:30` quando `consulta_automatizada_shopee=true` sem `autorizacao_api` | **INEXISTENTE** — não há endpoint público documentado para `shopee.com.br` sem auth; qualquer `GET https://shopee.com.br/api/...` não documentado é tratado como não autorizado | **POSSÍVEL com aprovação** — *Shopee Open Platform* / *Shopee Affiliate API* (ex.: `https://open-api.affiliate.shopee.com.br`) exige `appId + secret`, aprovação e rate limits; só chamar com `autorizacao_api=true` | **NÃO integrar scraping; se precisar dados Shopee, usar fluxo `MCA_AUTO_2.9.md:50` *Modo Recuperação*: usuário cola ficha/CSV; só chamar API oficial se tiver credenciais de afiliado aprovadas** |

**Conclusão:** scraping é bloqueado por contrato nos dois programas e dispara `FAIL` no Policy Engine. A única via escalável é **API oficial com credenciais de afiliado** (ML public + Shopee Open Platform), com backoff, cache e trilha de auditoria.

---

## 2. Base normativa verificada no repo

- `MDA AUTO/MCA_AUTO_2.9.md:50` — "nunca use busca/navegação automatizada para extrair dados do Mercado Livre"
- `MKT_Flow_3_0-1708-2251_v3.7.md:300` — `ML-PUBLIC-API-STATUS` = `UNKNOWN` quando `usa_api_publica_ml=true` (pendência 4.3(c))
- `policies/mercado_livre.json:47` e `shopee.json:30` — regras determinísticas não inferem ausência
- `MKTFLOW/policy_engine.py:184` — `UNKNOWN_SOFT` para `ML-PUBLIC-API-STATUS` permite draft com aviso, mas bloqueia `publish` se houver outro `UNKNOWN` real

---

## 3. Viabilidade técnica

### 3.1 Mercado Livre — API pública já implementada
- **Implementado:** `MKTFLOW/ml_client.py:31` `extrair_item_id()` `PADRAO_ITEM_ID:14` `consultar_api_publica_mercado_livre()` (timeout 5s, retry 3× exponencial, cache TTL 300s, erros nunca cacheados) + testes `tests/test_ml_client.py:1`
- **Campos retornados:** `titulo, preco, estoque, status, categoria_id, permalink, imagem, seller_reputation` — suficientes para `landing_generator.py:14` sem scraping
- **Limites:** 1 chamada por item a cada 5 min (cache) → ~12 req/h por item; HEAD de validação `link_validator.py:51` já respeita rate limit
- **Gap:** preço/estoque são voláteis (`MCA_AUTO_2.9.md:131` → revalidar após ~7 dias); `scheduler.py` + `alerts` (P1-4 futuro) devem re-checar

### 3.2 Mercado Livre — API oficial com OAuth (se confirmada)
- Endpoint afiliado/documentado: `https://api.mercadolibre.com/affiliate/...` (requer `access_token` de usuário afiliado) — não exposto no PDF fornecido; exigir prova
- Implementação proposta (se autorizada):
  ```python
  # MKTFLOW/ml_affiliate_client.py (não criar até confirmação)
  def fetch_affiliate_product(item_id: str, access_token: str) -> dict: ...
  ```
  Guardar `access_token` em `.env` (`ML_AFFILIATE_TOKEN`), nunca em log — estender `config_validator.py:22`

### 3.3 Shopee — Open Platform / Affiliate API
- **Hoje no repo:** nenhum cliente Shopee (`orchestrator.py:162` faz `SKIP` ML para Shopee, `mkt_flow_funcionalidades_extras.md` não lista API Shopee)
- **API oficial:** `POST https://open-api.affiliate.shopee.com.br/graphql` com `appId/secret` + assinatura; endpoints `productOffer`, `offerLink` retornam dados sem scraping
- **Implementação proposta (não fazer antes de ter credenciais):**
  ```python
  # MKTFLOW/shopee_client.py
  def consultar_shopee_afiliado(product_id: str, autorizacao_api: bool, timeout=5) -> dict:
      if not autorizacao_api:
          return {"status_politica": "FAIL", "regra_id": "SH-AUTOMATED-EXTRACTION"}
      # chama GraphQL com timeout/retry como ml_client.py
  ```
  Só chamar quando `consulta_automatizada_shopee=true` **e** `autorizacao_api=true` → `policy_engine.py` então avalia `SH-AUTOMATED-EXTRACTION: PASS` (hoje só há regra FAIL)

### 3.4 Por que não scraping?
- **Legal:** viola contrato → risco de ban do programa + perda de comissões acumuladas (pagamento mínimo R$30 + 3 compradores, validação até fim mês seguinte)
- **Técnico:** anti-bot (Cloudflare, `gz/account-verification` visto em `link_validator.py:51`) quebra seletores; manutenção contínua
- **Arquitetural:** viola decisão 1 (validação deve ser pré-processamento determinístico, não inference do LLM sobre HTML raspado)

---

## 4. Recomendação de integração (ordem)

1. **Imediato (sem novo código):** manter fluxo atual — ML via `ml_client.py:31` com aviso `ML-PUBLIC-API-STATUS` soft-UNKNOWN (`orchestrator.py:184`) e Shopee via colagem manual (`MCA_AUTO_2.9.md:56` Modo Recuperação). Solicitar por e-mail ao suporte afiliados ML texto: *"Uso da `GET /items/{id}` para preencher título/preço/imagem da landing do próprio link de afiliado com cache 5 min viola cl. 4.3(c)? Se não, por gentileza confirmar por escrito."* Guardar resposta como `policies/evidencia_ml_api_2026-08-28.pdf` e atualizar `policies/mercado_livre.json` de `UNKNOWN` para `PASS` se confirmado.

2. **Se ML confirmar:** promover `ml_client.py` de `UNKNOWN_SOFT` para `PASS` (remover tratamento soft em `orchestrator.py:184`), documentar `source` em `policies/mercado_livre.json:47`.

3. **Se precisar Shopee automatizado:** solicitar acesso `Shopee Affiliate Open API`; só então criar `MKTFLOW/shopee_client.py` espelhando `ml_client.py` (timeout, retry, cache, `autorizacao_api` flag). Até lá, manter `SH-AUTOMATED-EXTRACTION: FAIL` como guardrail.

4. **Não implementar:** nenhum `requests.get("https://www.mercadolivre.com.br/...")` com parsing HTML, nenhum `selenium/playwright` para Shopee, nenhum `mercadolivre.com/sec/` scraping.

---

## 5. Checklist antes de ativar nova API

- [ ] Credencial obtida no portal do afiliado (não chave pessoal do vendedor)
- [ ] Variável em `MKTFLOW/.env.example:1` + validada por `config_validator.py:22` (fail-fast, nunca loga valor)
- [ ] Regra correspondente em `policies/*.json` atualizada com `fonte` + `verified_at`
- [ ] Cliente com `timeout`, `retry` exponencial, `cache TTL`, `max_bytes` como `ml_client.py:31`
- [ ] Teste em `tests/test_*_client.py` cobrindo `401/429/5xx`, `timeout`, `cache hit`, `erro nunca cacheado`
- [ ] `policy_engine.py` cobre `usa_api_*` + `autorizacao_api` sem inferir ausência como `PASS`
- [ ] `dashboard.py` e `link_tracker.py` registram `origem: api vs cache`

---

## 6. Alternativa de curto prazo sem API

Seguir `MKT_Flow_3_0-1708-2251_v3.7.md:8` *Pendências*: para Shopee e para ML sem confirmação, pedir ao usuário ficha do anúncio (texto colado da página oficial) + `sheets_to_content.py:22` já aceita `produto_a_imagem`/`preco` via planilha — zero risco contratual.
