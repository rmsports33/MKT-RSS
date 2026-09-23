# Resumo da Sessão ConexoTech — 23/09/2026
Arquivo de transferência de contexto para nova conversa. Ler junto com `AGENTS.md` e `MEMORIA.md`.

## 1. Objetivo do projeto
Site de afiliação tech (conexotech.com.br) com tema próprio WordPress, fábrica de conteúdo RSS, automação de publicações via API e ferramentas de pesquisa.

## 2. Melhorias implementadas (sessões recentes)
- **Autor único Reinaldo Mendes** — regra salva na MEMORIA.md, bio oficial redigida, remoção de "| Redator" de títulos.
- **Preço S26 atualizado** — via API WordPress de R$ 7.191 para R$ 7.899.
- **Comparativos 9009/26** — convertidos para CPT, títulos limpos, conteúdo regenerado via API, regressão de câmera corrigida.
- **Categoria Notícias** — descrição atualizada via API.
- **Prefixos de arquivo** — filtro `conexo_archive_title_limpo` implementado em functions.php (viabiliza H1 limpo p/ Reviews/Notícias).
- **og:image fallback** — filtro `conexo_og_image_fallback` implementado (destacada ou screenshot.png).
- **Feed limpo** — `conexo_feed_clean` removendo chart.js/canvas/adsense do RSS.
- **Feeds separados** — links RSS para Reviews/Comparativos.
- **Schema Review S26** — JSON-LD com ratingValue 9.2 no ar.
- **Newsletter MailPoet** — formulário real ID 1 substituindo demo; código `[mailpoet_form id="1"]` no front-page.
- **CI do MKT-RSS consertado** — f-string Python 3.11, BOM em pipeline_p0.py, wiring links_internal; commit 20117da push realizado para rmsports33/MKT-RSS.
- **Plugin afiliados** — conexotech-affiliates v1.0.0 (endpoint /go/, tabelas cxaf_links/cxaf_clicks, admin, shortcode) e v1.1.0 (verificador cron de links quebrados).

## 3. Pendências (precisam de ação)
| Item | Responsável | Como destravar |
|---|---|---|
| Upload functions.php no Hostinger | Dono | File Manager ou FTP; arquivo local está em `site do projeto\conexotech\functions.php` |
| Breadcrumbs Rank Math | Dono | Ativar em Rank Math → Configurações gerais; ou aplicar fallback de código |
| Meta /blog/ | Nós depois do upload | Implementar via código ou Rank Math |
| Meta /category/noticias/ | Parcial | Descrição API aplicada; revisar no admin |
| Links afiliados reais ML/Shopee | Dono | Colar URLs reais nos reviews/comparativos |
| Pixel 10 Pro links | Dono | Criar/colar links de afiliado |
| Teste real newsletter | Dono | Inscrever e-mail e conferir recebimento |
| GSC indexação | Dono | Request Indexing nas URLs críticas |
| Ficha S26 specs oficiais | Nós | Comparar com fabricante e atualizar |
| Revogar senha triagem-1709 | Dono | Segurança |
| Páginas Sobre/Contato ajuste menu | Dono | Atualizar links do menu para novas páginas |

## 4. Próximos passos sugeridos
1. Upload functions.php + purge + validar og:image e títulos de arquivo.
2. Request Indexing no GSC das URLs home, /reviews/, /comparativos/, /sobre-nos/, review S26, /category/noticias/.
3. Verificar CI do repositório MKT-RSS pós-push.
4. Preencher links de afiliado reais e capas 1200px p/ comparativos.
5. Automatizar ponte `fontes_pesquisa.py` para fichas novas (aguarda credenciais de APIs de afiliados).
6. Futuro pós-receita: Creators API Amazon, Shopee Affiliate API, monitor de preços.

## 5. Ferramentas utilizadas
- **WordPress REST API** com `.env` (WP_URL, WP_USER, WP_APP_PASSWORD)
- **Hostinger File Manager / FTP** para uploads
- **Google Search Console** para indexação e monitoramento
- **Python 3.11** com scripts em `tools/`
- **Git + GitHub CLI** para versionamento
- **Rank Math** para SEO/sitemap
- **LiteSpeed Cache** (purge após uploads)
- **MailPoet** (newsletter)
- **Exa + Jina** (pesquisa com fontes primárias)
- UpdraftPlus (backup Google Drive)

## 6. Endereços de backup / repositórios
- **Repositório privado GitHub**: `rmsports33/-site-conexotech` (branch `master`) — push feito 18/09; últimas atualizações locais.
- **Clone de trabalho** `C:\Users\LIVE2PC\Desktop\MY PROJECTS FLOW` (MKT-RSS) — push do CI fix commit 20117da.
- **Tema local** `C:\Users\LIVE2PC\Desktop\site do projeto\conexotech\` — v1.3.1 com fallback og:image.
- **Backups de scripts** `C:\Users\LIVE2PC\Desktop\site do projeto\tools\` — todos os scripts versionados.
- **ZIPs de tema** `conexotech-v120.zip`, `conexotech-v132.zip` em `site do projeto`.
- **Plugin afiliados** `conexotech-affiliates-fase1-2026-09-21.zip` e `conexotech-affiliates-fase2-2026-09-21.zip`.

## 7. Auditorias realizadas (com relatórios)
- `tools/auditoria_fase1_2026-09-20.py` — auditoria inicial da Fase 1.
- `tools/auditoria_site*_2026-09-18.py` — varredura completa 11 URLs do sitemap, 11 achados.
- `tools/verifica_schema_pos_upload_2026-09-18.py` — validação pós-upload functions.php (7/7 OK).
- `tools/valida_feed_gate_2026-09-18.py` — gates RSS (9/9 aprovado).
- `tools/medir_leve_vs_completo_2026-09-18.py` + resultado JSON — LEVE 19/22 gate-correto, 86% economia.
- Re-auditoria 19/09 — newsletter real, schema íntegro, GSC cadastrado.
- Forense 10h28/2026 — snapshot OpenCode, blobs, restore git.

## 8. Automações vigentes
- **Daily RSS** (conta do dono) cria rascunhos diários categoria Notícias com gates, tags, imagem destacada, meta Rank Math.
- **Keyword research** integrado no pipeline RSS (`tema_keywords.json` + rewriter PT-BR).
- **Links internos** `tools/links_internos.py` → pipeline_rss anexa "Leia também".
- **Scripts pontuais** `aplicar_fase1`, `aplicar_bio`, `corrigir_*` via API WordPress.
- **Push GitHub** via PAT armazenado em `.env` (revogar tokens intermitentes).

## 9. Regras ativas para manter na nova conversa
- AGENTS.md e MEMORIA.md atualizados, incluindo:
  - Credenciais sempre em `.env`, nunca no chat.
  - Sinceridade 100%, pesquisar primeiro, duplas checam o já feito.
  - Autonomia permanente com limite de contas/servidor/publicação.
  - MVP grátis primeiro.
  - Explicar como para leigo.
  - Fontes primárias p/ artigos.

Nova sessão deve:
1. Ler AGENTS.md, MEMORIA.md e este arquivo.
2. Verificar estado atual do servidor (funções no ar? og:image? breadcrumbs?).
3. Executar pendência mais accessível primeiro.
4. Atualizar MEMORIA.md ao final.
