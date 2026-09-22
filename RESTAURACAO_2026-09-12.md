# RESTAURAÇÃO 12/09/2026 — registro honesto do incidente e da recuperação

## O que aconteceu
Comando de limpeza com `Remove-Item -Recurse` e combinação incorreta de parâmetros
(`-LiteralPath "."` + `-Include` sem `-Recurse`, PowerShell 5.1) apagou todas as
subpastas de `MY PROJECTS FLOW/` em vez de só `__pycache__`. Sem git na época,
sem lixeira (Remove-Item é permanente).

## O que sobreviveu no disco (arquivos da raiz)
`.env` (chaves), `mkt_flow_p0.db`, `mkt_flow.db`, `pipeline_p0.py`,
`requirements.txt` (com edição feedparser/trafilatura), tutorial, landings,
dashboards, clientes Drive, planilha modelo, PDFs/DOCXs da raiz.

## O que foi restaurado de backups
- `MKTFLOW/` — parcial: `MKTFLOW.zip` (MKT FLOW 3\backup_mkt_flow) é snapshot
  antigo (só módulos iniciais + prompts + `.env` + `mkt_flow.db` + venv).
  Faltavam 13 módulos → **reconstruídos** (ver abaixo). B1 reaplicado em `db.py`.
- `_arquivo/mkt-flow-escrita/` + base de `MDA AUTO/` — cópia integral de
  `site do projeto\mkt-flow-escrita` (12 arquivos).

## O que foi RECONSTRUÍDO (equivalente funcional, não byte-idêntico)
- `mkt_flow_p0/`: 18 módulos. 7 com conteúdo integral conhecido
  (config, policy_engine, api_ml, link_tracker, wp_publisher, dashboard, seo);
  `roi.py` idêntico ao doc v3.11; `validator/landing/scheduler/vault/alerts/
  keyword_research/health_check` reimplementados pelas specs (mesmas APIs,
  mesmos gates PASS/FAIL/UNKNOWN, mesmas regras — 21 regras portadas
  verbatim do doc v3.11 para `policies/*.json` + fallbacks).
- Novos (recuperados do trabalho da sessão): `rss_ingestor.py` (feeds
  corrigidos), `extractor.py` (download via requests), `rewriter.py`
  (env lazy, sem side-effect no import).
- `MKTFLOW/`: 13 módulos reconstruídos como adapters/funcionais
  (policy/landing delegam ao núcleo; demais standalone com DB próprio).
- `whois_tool/`: pacote mínimo (parser/robust/cache).
- `tests/`: 31 arquivos recriados (4 com conteúdo integral: roi_p0,
  landing_p0 com fix XSS/GA, e2e_p2, rewriter_p0; demais com cobertura
  equivalente de comportamento). Suíte: **125 passed**.

## Irrecuperável (declarado, sem backup localizado)
- `MKT_Flow_3_0-1708-2251_v3.6` … `v3.10`, `Mick_Assistente_MakDigital.md`,
  `MDA_piloto_revisao_estrutural.docx` (só o docx foi perdido; o .md equivalente
  existe na cópia), `redator-artigo-blogs/` (src+dados; outputs publicados
  seguem no ar em conexotech.com.br), `scripts/`, `docs/` antigos,
  `examples/`, outputs whois soltos, `00-gerador-schema*.zip`.
- Docs críticos recriados a seguir a partir do conteúdo integral conhecido:
  MANIFESTO, MKT_Flow v3.11, MCA 2.9, MDA Controlador, funcionalidades_extras,
  avaliacao_api, MKT_AUTO_3_0.

## Prevenção adotada
1. `git init` + commit nesta data (167 arquivos). `.env`, `*.db`,
   `token/credentials.json` fora do git (verificado via `git ls-files`).
2. Regra: nenhum comando destrutivo sem listar alvo + confirmação.
3. Backup zip local desta restauração ao lado deste arquivo (ver Desktop).
