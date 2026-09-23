# MEMÓRIA DE SESSÃO — MKT-RSS / MDA AUTO (conexotech.com.br)

> Arquivo de handoff para a próxima conversa/IA. Leitura obrigatória antes de trabalhar.
> Última atualização: 23/09/2026. Idioma do usuário: português. Fuso: BRT.

## 0. REGRAS PERMANENTES (nunca violar)

1. **Usuário leigo**: toda etapa que dependa exclusivamente dele exige tutorial passo a passo, clique a clique, sem jargão. Confirmar cada etapa antes de avançar.
2. **AGENTS.md**: sempre que trabalhar no projeto, pesquisar na internet ferramentas online similares com funções que o projeto não tem; registrar descobertas e avaliar incorporação.
3. **Commit por entrega**: commitar + push a cada entrega (houve reversão de worktree em 21/09 que apagou trabalho — ver §10.1).

## 1. IDENTIDADE DO PROJETO

- **Repo**: `https://github.com/rmsports33/MKT-RSS.git` — branch `master` — HEAD atual: `6fcab1a`
- **Site**: `https://conexotech.com.br` (WordPress no Hostinger, conta `reinaldocr210@gmail.com`)
- **Negócio**: automação de marketing de afiliados (foco: Mercado Livre; secundário: Shopee/Amazon/Magalu). Operação de 1 pessoa, R$ 0 de receita até aqui.
- **Pergunta-guia do projeto**: "Qual o menor ciclo que transforma 1 link de afiliado válido em R$ 1,00 de comissão — e o que trava esse ciclo hoje?"
- **Estrutura**:
  - `mkt_flow_p0/` — núcleo (validator, policy_engine 21 regras, landing, wp_publisher, seo/geo, roi, scheduler, vault, alerts, dashboard, keyword_research, rss_ingestor, extractor, rewriter, cloud_db/Turso, content_filter, links_internos)
  - `pipeline_p0.py` — CLI link afiliado → rascunho WP (BOM removido; dotenv só dentro do `main()`)
  - `pipeline_rss.py` — CLI RSS → rascunho WP (dotenv só no `main()`; roda 1x/dia via Actions `daily.yml`)
  - `MKTFLOW/site/bancada.html` — ferramenta de bancada (HTML estático; **nunca** colar HTML completo no editor WP — o WP remove o `<script>`)
  - `redator-artigo-blogs/` — pacote de redação (paralelo a `rewriter.py`; outra sessão mexe aqui — **não tocar sem checar `git status`**)
  - `_arquivo/` — legado arquivado (mkt-flow-escrita acadêmica, `mkt_flow.db` antigo, zips)
  - `MDA AUTO/` — specs v3.x; `docs/` — relatórios e tutoriais; `admin/` — Streamlit + bot Telegram + Dockerfile (nunca validado em produção); `whois_tool/`, `scripts/`
- **Segredos (FORA do git, só no disco)**: `.env` raiz + `MKTFLOW/.env` + `mkt_flow_p0/.env`, `.vault_key`, `credentials.json`. `.env` contém: `GA_MEASUREMENT_ID=G-FCBK1VGD90`, `WP_*`, `GROQ_*`, `TURSO_*` (da outra sessão), chaves Google.

## 2. MELHORIAS IMPLEMENTADAS NESTA SESSÃO (todas commitadas + push)

| # | O que | Arquivos | Commit | Verificação |
|---|---|---|---|---|
| 1 | Validador aceita formato novo ML (`wid`/`sid`/`polycard_client`, query **e** fragmento `#`) | `mkt_flow_p0/validator.py` | `6fcab1a` | link `#...&wid=...` → `PASS • destino: produto` |
| 2 | Gate social no Python (link `/social/` → FAIL), igual à Bancada | `mkt_flow_p0/validator.py` + 3 testes novos | `6fcab1a` | 12/12 validator |
| 3 | Testes herméticos anti-contaminação `TURSO_*` (e2e, pipeline_p0, rss_ingestor) | 3 arquivos de teste | `6fcab1a` | suíte 241 verdes 2x |
| 4 | Dashboard no DB oficial + migração `affiliate_runs` 249/249 + warnings (nunca silencioso) | `mkt_flow_p0/dashboard.py` | `648781b` | `affiliate_runs_classico: 249` (era 0) |
| 5 | Arquivamento: `_arquivo/` (mkt-flow-escrita, `mkt_flow.db`, zips), docx duplicado removido, refs atualizadas | vários | `648781b` | raiz limpa, reversível |
| 6 | GA4 nas landings (gtag + evento `affiliate_click`), `GA_MEASUREMENT_ID` no `.env.example` | `mkt_flow_p0/landing.py`, testes | `87a9eba` | 2 testes GA |
| 7 | `keyword_research.py` (Autocomplete Google, grátis, sem key) + 11 testes | novo + `tests/unit/` | `87a9eba` | sugestões reais com internet |
| 8 | GEO/AEO: `gerar_llms_txt()`, FAQ Schema, `enriquecer_com_keywords()`; pipeline gera `llms.txt` + `faq_<id>.json` | `mkt_flow_p0/seo.py`, `pipeline_p0.py` | `87a9eba` | testes seo |
| 9 | Bancada **v3.12**: sem campo de senha (era o flag do Google), senha via `prompt()` só na hora, IIFE anti-conflito, `noindex`, agendamento | `MKTFLOW/site/bancada-standalone.html` + `bancada.html` | `87a9eba` | `node --check` OK; ao vivo: script presente, sem `type=password` |
| 10 | Keywords Everywhere **removido** (conta com 0 créditos; chave testada e descartada) | deletados + `.env` limpo | sessões anteriores | 0 referências |
| 11 | Docs: `relatorio-seo-ferramentas.md` (5 tutoriais), `fix-rest-users.php` (snippet pronto) | `docs/` | vários | — |

## 3. PENDÊNCIAS (dono explícito)

**Do USUÁRIO (tutoriais já entregues no chat + `docs/relatorio-seo-ferramentas.md`):**
- P1. **Teste do "Gerador de links"** (responder letra A–E — ver §6). É o gargalo nº 1.
- P2. Colar `docs/fix-rest-users.php` no `functions.php` do tema → avisar p/ **re-teste ao vivo** do endpoint.
- P3. `robots.txt` + `Disallow: /bancada/`; apagar página WP `/bancada/` (manter só `bancada.html` estático); Search Console → Pedir revisão → aguardar 1–3 dias.
- P4. Re-enviar `bancada.html` ao Hostinger após cada edição local + `Ctrl+F5` (cache LiteSpeed agressivo).
- P5. Decidir backup Drive (OAuth `python scripts/backup_drive.py`) vs oficializar só git.

**Da PRÓXIMA SESSÃO (código):**
- P6. Religar `marketplaces.json` ao `validator.py` **ou** deletar o arquivo (hoje: morto no Python; só o JS da Bancada tem a lista de 18 plataformas).
- P7. Recriar `docs/pesquisa-afiliacao.md` se precisar (perdido na reversão 21/09).
- P8. Congelar `MKTFLOW/` clássico (só leitura); repo próprio p/ escrita acadêmica exige `gh auth login` (CLI presente, não autenticado).
- P9. Verificar status dos 5 workflows Actions (backup, ci, daily, keepalive, pages).

## 4. PRÓXIMOS PASSOS (ordem)

1. Letra A–E do Gerador de links → 1º link `wid` → Bancada PASS → rascunho → publicar **1º review** (primeira comissão = teste de aceitação do projeto).
2. Fechar segurança (P2+P3) e confirmar revisão do Google.
3. Rotina: 2 reviews/semana via `python -m mkt_flow_p0.keyword_research "<produto>"`.
4. Regra de eficiência: nenhuma feature nova sem responder "isso aproxima a próxima comissão?".

## 5. FERRAMENTAS UTILIZADAS

Python 3.14 + pytest (38 arquivos, **241 testes, suíte verde**), node (`--check` p/ JS), git (+push), Hostinger File Manager, wp-admin, Search Console, GA4, Chrome Web Store (extensões verificadas: Melify 5.0, Afiliado Dash 5.0, LucreShop 3.0, AffiliateX 4.5★/9k installs, Block Yourself from Analytics), API Keywords Everywhere (testada: 402 sem créditos → descartada), Autocomplete Google, websearch/webfetch (docs ML, Reclame Aqui, GitHub open-source: serpbear, open-seo, searchstack-aeo).

## 6. TESTE DO "GERADOR DE LINKS" (contexto p/ retomar)

- Conta ML `reinaldomcarvalho` ativa (4 cliques, R$0); registrada via Facebook antes do site.
- Caminho certo: Central → Ferramentas → **Gerador de links** (ícone seta azul) — NÃO "Gerador de produtos recomendados" (gera link de perfil, bloqueado por desenho). Só no **PC**, só em **página de anúncio** (nunca busca/categoria/ofertas/vendedor), etiqueta `conexotech`, **copiar na hora** (link some).
- Gabarito: `PASS • destino: produto`. Matriz: A=botão cinza (campo vazio) · B=erro/página restrita → trocar de produto · C=gira → aba anônima/PC · D=sem `wid` → gerador errado · E=não passa na Bancada → link `/social/` ou sem tag.
- Sair e refazer filiação: **desaconselhado** (risco "mais de uma conta" nos termos + perde etiqueta + refila aprovação). Só via suporte e em último caso.

## 7. BACKUPS (todos os endereços)

- **GitHub** `rmsports33/MKT-RSS` branch `master` (oficial interino): `6fcab1a`, `20117da`, `648781b`, `871be88`, `17d9ad2` ("reversão worktree" 21/09) …
- **Google Drive**: NÃO configurado (`scripts/backup_drive.py` trava no OAuth de browser).
- **Local `_arquivo/`**: mkt-flow-escrita, `mkt_flow.db` (legado, `affiliate_runs` migrada), 3 zips (1 corrompido/0 bytes).
- DB oficial: `mkt_flow_p0.db` (git-ignored). Outputs: `dashboard_p1.*`, `sitemap.xml`, `llms.txt`, `landing_*.html`, `faq_*.json`.

## 8. AUTOMAÇÕES (site + artigos)

- `pipeline_p0.py`: valida → API ML → policy → ROI → landing(+GA4) → SEO check → keywords → FAQ → llms.txt → WP draft/future → tracker → sitemap. Gate: só `PASS` publica.
- `pipeline_rss.py` + `daily.yml`: RSS → gate pauta → extractor → rewriter(Groq) → capa → rascunho WP (usa Turso na nuvem).
- Bancada v3.12 (`public_html/bancada.html`): valida → gera/agenda rascunho via REST (senha via `prompt`, nada salvo).
- WP: Rank Math + Site Kit (GA4+Search Console) + AffiliateX instalados pelo usuário.

## 9. AUDITORIAS E RELATÓRIOS (nesta sessão)

1. **Segurança WP** (ao vivo): home/sitemap/8 URLs limpos; sem cloaking; dirs 403; **`/wp-json/wp/v2/users` AINDA expõe logins (re-testado hoje, 200)** → fix em `docs/fix-rest-users.php`, aplicação pendente. Senha de aplicativo exposta no chat → **testada hoje: 401 (morta)**. Causa provável do flag "páginas fraudulentas": campo de senha público da Bancada → removido na v3.12.
2. **Estrutural**: 8 erros (ferramenta>negócio, gargalo externo adiado, 2 implementações, luta anti-WP, segurança tardia, 68 arquivos sem commit, métricas sem tráfego, escopo antes da receita) — correções em §2.
3. **Validador**: link `wid` perfeito reprovado (regressão da reversão) → corrigido + 3 testes.
4. **Suíte**: 2 falhas intermitentes no RSS → causa raiz: `main()`+`load_dotenv` polui `os.environ` com `TURSO_*` (.env da outra sessão) e `rss_ingestor._nuvem()` ia p/ nuvem → fixtures herméticas nos 3 arquivos.
5. **Pesquisas web**: 10+10 marketplaces/afiliação; keywords gratuitas; extensões Chrome; plugins WP; casos ML Gerador de links (Reclame Aqui + ajuda oficial).

## 10. ARMADILHAS (ler antes de agir)

1. **Sessões concorrentes**: commits externos no log; `redator-artigo-blogs/*.py` modificado AGORA (não é desta sessão — **não commitar sem checar**). Regra: `git status` antes de `git add`.
2. **PowerShell 5.1**: sem `&&`, sem heredoc, aspas quebram `python -c` com regex → usar `.py` em `C:\Users\LIVE2PC\AppData\Local\Temp\opencode\`.
3. **Ruídos**: `PermissionError` do pytest no tmp do Windows = ignorar; contagem de testes flutuou (235–241) por churn de arquivos.
4. **Bancada**: sempre arquivo estático; `Ctrl+F5` + purge LiteSpeed após upload; `node --check` no `<script>` extraído.
5. **Nunca PASS por inferência** (UNKNOWN ≠ PASS); Shopee (`s.shopee.com.br`) = UNKNOWN com mensagem própria.
6. `.env` (com TURSO_*) muda comportamento dos testes — fixtures herméticas existem só nos 3 arquivos; ao criar teste que chama `main()`, replicar o fixture.
