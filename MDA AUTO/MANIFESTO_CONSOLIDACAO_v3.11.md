# MKT Flow — Manifesto de Consolidação (v3.11)

**Data:** 30/08/2026
**Decisão:** consolidar as duas implementações paralelas em um único núcleo e separar o domínio acadêmico.

## Problema detectado (auditoria completa 28/08/2026)

O projeto cresceu com **duas implementações paralelas** do mesmo domínio:

| | A — `mkt_flow_p0/` | B — `MKTFLOW/` (clássico) |
|---|---|---|
| Entrypoint | `pipeline_p0.py` | `orchestrator.py` |
| DB | `mkt_flow_p0.db` | `MKTFLOW/mkt_flow.db` |
| Validador | `validator.py` | `link_validator.py` |
| Policy | `policy_engine.py` + JSON pacote | `policy_engine.py` + `policies/*.json` |
| Landing | `landing.py` (str) | `landing_generator.py` (dict) |
| Dashboard | `dashboard.py` | `dashboard.py` + `dashboard.html` |

Custo: cada correção de compliance precisava ser feita 2x; APIs incompatíveis (`resolve` vs `resolver_redirect`, str vs dict).

## Bug crítico corrigido (B1)

`orchestrator.py` gravava em `affiliate_runs`, mas `MKTFLOW/db.py` não criava a tabela.
Evidência: `health_check.py` retornava `{'ok': False, 'erro': 'tabela affiliate_runs ausente'}` e o pipeline real
exibia `no such table: affiliate_runs`.
**Correção:** `MKTFLOW/db.py` agora cria `affiliate_runs`, `campaigns`, `link_publications` (schema do `link_tracker.py`)
e `platform_schedules` (schema do `scheduler.py`). `health_check` retorna `ok: True`. 212 testes PASS.

## Decisões aprovadas (30/08/2026)

1. **Núcleo único = `mkt_flow_p0/`** — o módulo A é o núcleo consolidado.
2. **Domínio acadêmico separado = `_arquivo/mkt-flow-escrita/`** — docs MDA/EAC/Prompt-Mestre/MCA foram movidos
   (copiados) para pasta própria, fora do pipeline de afiliados.
3. **Segredos/backups fora de produção** — `MKTFLOW.zip` (127 MB), `mkt_flow_backup_*.zip` (534 MB),
   `token.json`, `MKTFLOW/credentials.json` movidos para `C:\Users\LIVE2PC\Desktop\arquivos_mkt_flow\`.
   `.gitignore` ampliado: `*.zip`, `*.bak`, `.vault_key`, `MKTFLOW/output/`.

## O que foi feito na consolidação (v3.11)

- `mkt_flow_p0/policies/{mercado_livre,shopee}.json` — fonte canônica portada de `MKTFLOW/policies/`
  (com `fonte` por regra, 14 ML + 7 Shopee).
- `mkt_flow_p0/policy_engine.py` — carrega das `policies/*.json` com fallback para `policy_rules.json` (v3.6).
- `mkt_flow_p0/health_check.py` — verificação integrada (env/DB/policy/WP).
- `mkt_flow_p0/validator.py` — aceita `resolve` (alias do clássico) e `resolver_redirect`.
- `mkt_flow_p0/landing.py` — `gerar_landing_page_completa()` retorna dict rico
  (html/slug/url_amigavel/meta), mantendo `gerar_template_landing_page()` (str).
- `_arquivo/mkt-flow-escrita/` — pasta separada com README + docs acadêmicos.

## Estado após consolidação

- **212 testes PASS** (inclui as duas implementações — nenhum teste alterado).
- Pipeline A e B rodam e **persistem** (afiliate_runs: 82 runs, 41 publications históricas).
- Health check integrado funcional.

## Próximos passos (pendências)

- **P0 pendência compliance:** confirmar por escrito com suporte ML se `GET /items/{id}` viola cl. 4.3(c)
  (`ML-PUBLIC-API-STATUS` segue UNKNOWN; `avaliacao_api_oficial_vs_scraping.md`).
- **P1:** comissão por categoria (dado de fonte, não inventar) — pedir ao usuário.
- **P2:** `shopee_client.py` só com credenciais de afiliado aprovadas.
- **Deprecar B (MKTFLOW/ clássico):** manutenção a partir de agora apenas no núcleo `mkt_flow_p0/`;
  B fica como referência/histórico até migração completa.
