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

## 21/10/2026 (M04.16E) — gate do MKT-RSS integrado, testado e medido

- PR #5 merged no `MKT-RSS`: `dbc8cf0` (gate de valor fail-closed). PR #6
  merged: `5a9e06a` (gate integrado no `pipeline_rss`, opt-in). Branches de
  origem preservadas para reversão (`0202970` e `389e56e`).
- Suíte completa no master mesclado: **403 passed**. CI verde nos runs
  `39650465426` e `39672743171`.
- Auditor adversarial novo no MKT-RSS (`tools/2026-10-21_auditar_gate_valor.py`):
  passa 23/23 no estado corrigido e REPROVA a versão fail-open (exit 1, 8
  divergências). Medição nova (`tools/2026-10-21_medir_gate_no_rss.py`): com o
  gate ligado no caminho RSS, **7/7 feeds** de `FEEDS_PADRAO` são bloqueados
  (o preço exige marketplace e a fonte primária exige fabricante, e nenhum vem
  de feed). Motivo material para manter `GATE_PUBLICACAO_ENABLED=false`.
- Correção no PR #6: `.env.example` com bloco de comentário duplicado — limpo.
- Erro meu, correção e trava: o auditor afirmava que dois cenários tinham que
  dar BLOQUEADO; a expectativa estava errada (o gate é "≥1 dos 4 critérios" e
  o que não pode é o critério indevido ser concedido). Corrigido para
  asserções explícitas sobre o contrato, e reexecutado nos dois lados para
  garantir que continua reprovando a versão antiga.
- Nenhum deploy, nenhuma publicação, nenhuma escrita no WordPress.
  `GATE_PUBLICACAO_ENABLED` continua `false` (varredura do repositório inteiro).
- Pendências que continuam abertas: evidência **por produto** (Issue #9), o
  adaptador `gerar_comparativo` → `create_comparativo`, e o fechamento do
  `wp_publisher`.

## 21/10/2026 (M04.17A) — validacao de evidencia POR PRODUTO (Issue #9, 2o requisito)

- Defeito corrigido: o gate recebia o TEXTO INTEIRO e varria o conjunto, entao
  um unico preco com data no texto approveva um comparativo de varios
  produtos. Medido: "Galaxy S26 vs Pixel 11" com o preco SO do S26 passava com
  `preco_br_data`.
- Regra implementada: **evidencia de um produto nunca aprova outro**. Cada
  produto e' avaliado isoladamente (preco, data, links, medicao, video proprios)
  e TODOS precisam ter valor acrescentado. No modo por produto o texto geral
  NAO participa do veredito — sem isso a contaminacao voltaria pela porta do
  texto.
- Contrato ADITIVO (o aprovado no M04.16C nao muda): novos parametros
  `produtos=None` e `exigir_produtos=False`; saidas novas
  `evidencia_por_produto`, `criterios_por_produto`, `produtos_sem_valor`. O
  modo texto continua e DECLARA que a validacao por produto nao foi aplicada
  (lacuna visivel, nao silenciosa). `exigir_produtos=True` bloqueia quando a
  lista nao vem (modo do fluxo comparativo).
- Verificacao: suite completa **423 passed** (403 do M04.16E + 20 novos em
  `tests/unit/test_content_filter_produto_p0.py`), sem alterar nenhum teste
  anterior. O auditor adversarial passou a EXIGIR a validacao por produto:
  reprova a implementacao do M04.16C (exit 1, 5 divergencias) e passa 28/28
  com o M04.17A.
- Erro meu, correcao e trava: o primeiro `_avaliar_por_produto` quebrava com
  `AttributeError` quando a lista recebia algo que nao fosse dicionario (o
  nome do produto era lido antes do validador). Correcao: extracao do nome
  tolera qualquer tipo. Trava: entrada malformada vira BLOQUEIO, nunca
  excecao — excecao num gate fail-closed vira passagem indevida.
- Entregue em branch `feat/m0417a-evidencia-por-produto`, commit `79ff60b`,
  **PR #7 ABERTO** (CI verde, run `39674868934`). Merge NAO executado: o
  Issue #9 mantem o guardrail "proibir auto-merge", entao a integracao fica
  para autorizacao especifica.
- Continuam abertos: onde ligar o gate (M04.17D — hoje bloqueia 7/7 feeds no
  caminho RSS, medido), adaptador `gerar_comparativo` -> `create_comparativo`
  (M04.17B), contrato do `wp_publisher` (M04.17C) e a coleta com snapshot
  persistido (evidencia por produto na origem).
- Sem deploy, sem ativacao do gate (`GATE_PUBLICACAO_ENABLED` segue false),
  sem publicacao, sem escrita no WordPress.

## 21/10/2026 (M04.17A integrado) — PR #7 merged no master do MKT-RSS

- **Merge supervisionado (ordem explicita do dono): PR #7 -> `5a79fc6`** em
  `rmsports33/MKT-RSS` (squash). Branch de origem preservada para
  rastreabilidade e reversão: `feat/m0417a-evidencia-por-produto` (`8530d41`).
- Criterios verificados antes do merge: PR `MERGEABLE/CLEAN`; CI verde no run
  `39679344510`; sem conflito (`git merge-tree` exit 0); **nenhuma credencial
  no diff** (varredura por senha/token/chave/JWT); 6 arquivos esperados e
  nenhum inesperado; suite completa **426 passed**; auditor adversarial
  **28/28** (e REPROVA a implementacao M04.16C, exit 1).
- **Compatibilidade do contrato legado M04.16C: PROVADA, nao presumida.**
  `tools/2026-10-21_compatibilidade_m0416c.py` carrega a versao antiga e a nova
  e compara: 23 casos legados com veredito e criterios IDENTICOS, 7 chaves
  legadas preservadas, 1 chave aditiva (`evidencia_por_produto`). Reexecutado
  depois do merge contra o commit pre-merge `8f7ad61`: COMPATIVEL, exit 0.
  Alem disso, 3 testes no CI que nao dependem da versao antiga (preservacao
  de chaves, chamada posicional antiga ainda valida, chaves legado do
  `gate_publicacao`).
- Erro meu, correcao e trava (segundo do turno): meu teste de compatibilidade
  do `gate_publicacao` usou o conjunto de chaves do `filtrar_valor_
  acrescentado`. Correcao: `gate_publicacao` devolve a FUSAO do compliance com
  o valor, entao o conjunto legado dele e' outro. Trava: compatibilidade se
  prova comparando implementacoes, nao conferindo de memoria.
- Estado do Issue #9 apos esta integracao: o 2o criterio objetivo (evidencia
  por produto) esta IMPLEMENTADO, PROVADO e INTEGRADO. A issue continua
  ABERTA porque a evidencia por produto ainda nao vem da ORIGEM (o modulo
  valida o que o chamador declara; o coletor ainda nao garante preco e data
  de cada produto — snapshot persistido segue pendencia do M04.16).
- Restricoes mantidas: sem deploy, sem ativacao do gate
  (`GATE_PUBLICACAO_ENABLED` segue `false`), sem publicacao, sem escrita no
  WordPress, nenhum worktree de outra sessao alterado.
- Proxima etapa: **M04.17B — adaptador `gerar_comparativo` ->
  `create_comparativo`**, em branch isolada, sem merge nem deploy automatico.

## 21/10/2026 (M04.17B) — adaptador `gerar_comparativo` -> `create_comparativo`

- O problema: o redator devolve PAGINA HTML COMPLETA (`<!DOCTYPE>`, `<html>`,
  `<head>` com JSON-LD, `<body>`) e o `wp_publisher` mandava isso no
  `content`, criando `post_type=post`. O MCP `create_comparativo` espera
  campos estruturados. Pior: a EVIDENCIA se perdia no caminho — preco, data
  de captura e fonte ficavam espalhados no HTML, e o gate por produto nao
  conseguia provar nada.
- Entregue: `mkt_flow_p0/comparativo_contract.py` — o CONTRATO estruturado
  que carrega a evidencia de CADA produto (preco, data_captura, fonte_preco,
  fonte, ficha, evidencia_video, evidencia_medicao, nota, compra) e quatro
  funcoes: `construir_contrato`, `validar_contrato` (estrutural, fail-closed),
  `avaliar_contrato` (estrutural + gate POR PRODUTO do M04.17A) e
  `contrato_para_mcp` (parametros exatos de `create_comparativo`, levanta
  `ContratoInvalido` se o contrato nao passar).
- Decisoes do adaptador: (1) o `content` e' so o CORPO — `extrair_corpo_html`
  tira doctype/html/head/script, e documento completo remanescente e' ERRO;
  (2) a data ISO do redator vira DD/MM/AAAA e e' validada de verdade
  (`2026-02-31` nao vira evidencia); (3) preco SEM link de marketplace nao e'
  evidencia — o contrato avisa, e o gate nao aprova; (4) mais de 3 produtos
  (ou 6 criterios) e' ERRO, porque o `array_slice` do MCP trunca em SILENCIO
  e perderia a evidencia; (5) `products`, `notas` e `buys` sao construidos
  da MESMA lista, na mesma ordem — e o que impede dessincronia entre produto,
  nota e link de compra.
- **A REGRA DO COMPARATIVO (a mais importante):** o gate generico aprova um
  produto que so tem `fonte_primaria`, e em comparativo isso e' fraco — a
  ficha do fabricante ja existe, e repetir e' o "replicated content" da
  SQRG 4.6.6. Por isso `avaliar_contrato` exige POR PRODUTO ao menos um de
  `preco_br_data`, `video_transcrito`, `medicao_propria` ou
  `cruzamento_2fontes`. A regra fica no adaptador (que sabe que o fluxo e'
  comparativo) e NAO altera o gate generico aprovado no M04.16C/M04.17A.
- Verificacao: suite completa **456 passed** (426 do M04.17A + 30 novos em
  `tests/unit/test_comparativo_contract_p0.py`), sem alterar teste anterior.
  `tools/2026-10-21_conferir_contrato_mcp.py` conferiu o contrato contra o
  CATALOGO PUBLICO DO MCP REAL (nao contra a copia local do PHP): o servidor
  declara `title, content, products, notas, crits, veredito, buys, cat_slug` e
  o adaptador gera exatamente essas 8 chaves, nos limites (3 produtos, 6
  criterios). Exit 0.
- Erros meus do turno: (1) eu esperava que o GATE reprovasse o produto sem
  preco — ele APPROVA (via `fonte_primaria`), e foi essa leitura que
  mostrou a falta da regra do comparativo; o teste agora fixa as DUAS
  camadas (gate aprova, regra do comparativo reprova). (2) o script de
  conferencia falhou com "ferramenta nao encontrada" porque o catalogo do MCP
  publica o nome na chave `tool`, nao `name`.
- Entregue em branch `feat/m0417b-adaptador-comparativo`, **PR #8 ABERTO**,
  **sem merge** (guardrail "proibir auto-merge" do Issue #9). Sem deploy, sem
  ativacao do gate (`GATE_PUBLICACAO_ENABLED` segue false), sem publicacao,
  sem escrita no WordPress.
- Continuam abertos: a CHAMADA MCP em si (o MKT-RSS nao tem cliente MCP —
  verificado por varredura: nenhuma ocorrencia de `mcp`/`conexo/v1` no
  repositorio), o `wp_publisher` (ainda manda documento inteiro e cria
  `post_type=post` — M04.17C), a evidencia na origem (o `price_history` do
  redator nao traz a origem do preco), e onde ligar o gate (M04.17D).

## 21/10/2026 (M04.17C) — escrita de comparativo no WordPress via MCP (PR #9 aberto)

- Auditoria do `wp_publisher`: o caminho efetivo e' `POST
  {wp_url}/wp-json/wp/v2/posts` (tipo fixo `post`), payload
  title/content/status, gate `publish` so com `status_validacao == PASS` (senao
  forca draft). Chamadores: `pipeline_rss.py:130` (sempre draft) e
  `pipeline_p0.py:170`. **Nao existe cliente MCP no MKT-RSS** (verificado por
  varredura: nenhuma ocorrencia de `mcp`/`conexo/v1` no repositorio).
- Descoberta que definiu a solucao: o CPT `comparativo` e' registrado com
  `show_in_rest => true` mas **SEM `meta`**, entao `_conexo_prod_*`,
  `_conexo_nota_*`, `_conexo_buy_*` e `_conexo_crit_*` NAO sao gravaveis pelo
  REST — e o `single-comparativo.php` depende delas para montar a tabela. Um
  comparativo criado por `POST /wp/v2/comparativo` nasceria SEM a tabela.
  Quem escreve esses campos e' o servidor MCP, no PHP.
- Entregue: `executar_ferramenta_mcp(...)` e `publicar_comparativo(...)` em
  `mkt_flow_p0/wp_publisher.py`, com o **caminho legado byte-identico** (diff
  100% acrescimo: 119 linhas, ZERO remocao). `publicar_comparativo` valida o
  contrato (estrutural + gate por produto do M04.17A), recusa documento
  completo no `content` (fail-closed na fronteira de escrita), chama o MCP
  `create_comparativo` e confere `post_id` + `status == draft` (status
  diferente e' erro explicito, com o post_id junto). **Sem dependencia nova**:
  `requests` ja era do projeto; sem servico pago.
- Testes: 20 novos, tudo mockado, nenhum post criado. Contrato (endpoint,
  ferramenta, 8 parametros, tabela alinhada, `content` so o corpo, auth),
  REGRESSAO do legado (assinatura via `inspect.signature`, `/wp/v2/posts`,
  publish sem PASS bloqueado, UNKNOWN forcando draft, `/wp/v2/pages`) e
  FALHAS (contrato sem evidencia e documento completo com ZERO requisicao;
  MCP recusa, sem post_id, status publicado; 500; timeout; nao-JSON; excecao).
- Suite completa: **480 passed** (460 do M04.17B + 20). Entregue em branch
  `feat/m0417c-escrita-comparativo`, **PR #9 ABERTO**, **sem merge**
  (guardrail "proibir auto-merge" do Issue #9).
- Sem deploy, sem ativacao do gate (`GATE_PUBLICACAO_ENABLED` segue false),
  sem publicacao, sem escrita no WordPress.
- Continuam abertos: **o pipeline ainda nao chama `publicar_comparativo`**
  (nada no pipeline_rss/pipeline_p0 a invoca ainda — ligar isso e' M04.17D, junto
  com a posicao do gate); a evidencia na origem (o `price_history` do redator
  nao traz a origem do preco); e verificar se o caminho de NOTICIAS tambem
  produz documento inteiro (o review 9183 saiu com HTML quebrado).

## 21/10/2026 (M04.17D) — ligacao operacional do pipeline: redator -> WordPress (PR #10 aberto)

- Ponto de integracao: o caminho de NOTICIAS (`pipeline_rss.py` ->
  `publicar_no_wordpress` -> `POST /wp/v2/posts`) e o de COMPARATIVO sao
  pipelines diferentes, e o comparativo NAO existia no MKT-RSS: o
  `gerar_comparativo` mora no redator e devolve pagina HTML completa, e o
  MKT-RSS so sabia publicar `post`. A ligacao e, portanto, um FLUXO NOVO E
  SEPARADO (`mkt_flow_p0/comparativo_flow.py`), com a validacao de valor na
  posicao certa: DEPOIS da coleta e do enriquecimento de evidencias, nunca
  sobre feed RSS bruto (a medicao do M04.16E provou que ali o gate bloqueia
  7/7 feeds).
- Cadeia: `auditar_precos` -> `construir_contrato` -> `validar_contrato` ->
  `avaliar_contrato` (gate por produto) -> `publicar_comparativo` (MCP,
  rascunho).
- Duas travas independentes: **dry-run por padrao** (`dry_run=True` e' o
  padrao; sem `dry_run=False` nenhuma requisicao e' feita) e **opt-in por
  configuracao** (`COMPARATIVO_PUBLICACAO_ENABLED` em {1,true,yes,on};
  ausente ou com outro valor -> "desativado", sem requisicao). O gate NAO foi
  flexibilizado: produto sem evidencia propria e' bloqueado ANTES de
  qualquer requisicao ao WordPress.
- **Investigacao da origem dos precos:** hoje NADA captura preco junto com a
  origem. O redator nao tem produtor de `price_history` (so consumidor) e os
  coletores dele BLOQUEIAM marketplaces; no MKT-RSS, `marketplaces.json`
  existe mas NAO e' usado por nenhum `.py` (e' configuracao do fluxo de
  afiliacao, nao coletor). O `price_history` e' entrada externa/manual. O
  adaptador exige as tres provas por produto (marketplace + data de coleta +
  vinculo inequivoco) e nao inventa o que falta: preco sem marketplace vira
  aviso e o comparativo e' bloqueado; preco de produto inexistente e' ERRO
  (evidencia solta nao pertence a ninguem); ponto com nome de produto
  divergente e' ERRO.
- **Defeito encontrado no dry-run com dado real:** o criterio `preco_br_data`
  — o principal da regra 13 — era INALCANCAVEL pela cadeia real. O contrato
  guardava o preco como "5.999,00" (o `normalizar_preco` tira o simbolo) e a
  regex do gate EXIGE "R$": "5.999,00" nao casa. Nenhum teste anterior pegou
  porque o comparativo do M04.17B ja passava pelo criterio de cruzamento.
  Correcao: o produtor passou a guardar o preco no formato que o gate le
  ("R$ 5.999,00"). **O gate NAO foi afrouxado** (mudar a regex dele aceitaria
  numero solto no texto, que e' falso positivo). Prova:
  `tools/2026-10-21_provar_preco_br_data.py` (antes: False; depois: True).
  Contraprova: preco sem marketplace CONTINUA sem o criterio.
- Segunda lacuna fechada: um contrato sem nenhum criterio criaria post sem
  tabela; `validar_contrato` agora exige pelo menos um criterio.
- Caminho de NOTICIAS verificado separadamente: o defeito de HTML completo
  (review 9183) era EXCLUSIVO da pagina do redator. O caminho de noticias usa
  `markdown_para_html`, que produz FRAGMENTO (sem doctype/html/head/body) —
  o contrato legado nao precisa mudar, e uma trava nova impede que mude sem
  querer.
- Verificacao: suite completa **504 passed** (480 do M04.17C + 24 novos).
  Os 3 testes do M04.17B que falharam foram atualizados no FORMATO do preco
  ("5.999,00" -> "R$ 5.999,00"); nenhuma assercao de comportamento mudou.
  Auditor adversarial: exit 0.
- **Dry-run real** (CLI, `tools/exemplo_comparativo_m0417d.json`):
  `dry_run_ok`, `escreveu: false`, os dois produtos com 3 criterios
  (`preco_br_data`, `fonte_primaria`, `cruzamento_2fontes`) e os vinculos de
  preco explicitos por produto. **Dry-run negativo**
  (`tools/exemplo_comparativo_sem_marketplace_m0417d.json`): `bloqueado` com
  `sem_valor_por_produto` e o diagnostico exato. Nenhuma requisicao em
  nenhum dos dois.
- Branch `feat/m0417d-pipeline-comparativo`, **PR #10 ABERTO**, **sem merge**
  (M04.17D nao autorizado para merge). Sem deploy, sem ativacao do gate
  (`GATE_PUBLICACAO_ENABLED` segue false), sem publicacao, sem escrita no
  WordPress.
- Continuam abertos: **a origem do preco ainda nao existe** (sem ela, o
  criterio de preco so vale com `price_history` fornecido a mao);
  `gerar_comparativo` ainda nao chama este fluxo (falta o lado do redator
  entregar `modelos`/`price_history` estruturados); onde ligar o gate no
  fluxo de noticias (o feed deve virar digest, nao artigo); e a validacao
  de ponta a ponta contra o WordPress, que exige autorizacao especifica.
