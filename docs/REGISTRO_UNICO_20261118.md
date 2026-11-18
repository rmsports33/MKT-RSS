# Registro único de funcionalidades e status — 18/11/2026

Fonte única para auditorias. Evita reler documentação dispersa.
Detalhes por tema permanecem nos documentos citados.

## 1. WordPress (plugins)

| Plugin | Versão | Status | Observação |
|---|---|---|---|
| conexo-editorial-gate | 0.1.0-rc10.4 | **ativo** | Gate Único; recebeu trava de proveniência |
| conexo-hmac-vault | 0.1.0 | ativo | Assinatura HMAC, chave no WP Vault |
| conexo-native-seo | 0.5.2 | ativo | — |
| conexo-native-seo (mu) | 0.5.1 | inativo | duplicado |
| conexotech-affiliates | 1.11.1 | ativo | class-checker via oEmbed |
| git-installer | 1.3.4 | ativo | — |
| hostinger-affiliate-plugin | 3.0.57 | ativo | — |
| jetpack | 16.3.1 | ativo | — |
| litespeed-cache | 7.9.2 | ativo | — |
| mailpoet | 5.44.0 | ativo | — |
| post-type-switcher | 4.1.1 | ativo | — |
| seo-by-rank-math | 1.0.280 | ativo | SEO público |
| google-site-kit | 1.190.0 | ativo | — |
| updraftplus | 1.26.14 | ativo | — |
| wordpress-importer | 0.9.7 | ativo | — |
| wp-consent-api | 2.1.0 | ativo | — |
| conexo-gate-agenda-nativa | 0.3.3 | **inativo** | legado; causa fatal se ativado (função duplicada) |
| hostinger-preview-domain | — | must-use | reescrita de host em XML-RPC/REST |

## 2. Módulos do motor MKT-RSS

| Módulo | Status | Observação |
|---|---|---|
| `editorial_import.py` | ativo | entrada canônica; gera manifesto e marca de proveniência |
| `editorial_provenance.py` | ativo | marca + validação do pacote |
| `editorial_video.py` | ativo | bloco de vídeo, curadoria humana obrigatória |
| `editorial_transport.py` | ativo | transporte assinado HMAC |
| `editorial_broker_transport.py` | ativo | publicação via broker, só publish/schedule |
| `wp_draft_staging.py` | ativo | cria rascunho com readback |
| `seo.py` / `seo_contract_native.py` / `seo_delivery_signing.py` | ativo | SEO nativo; assinatura bloqueada por chave ausente |
| `editorial_substance.py` | ativo | avaliação substantiva por critérios |
| `image_protocol.py` | ativo | protocolo de imagem |
| `editorial_readiness.py` | ativo | prontidão editorial |
| `release_guard.py` / `origins.py` | ativo | unificados |
| `triagem_decisoes.py` | ativo | decisão supervisionada, auditoria imutável |
| `conexo_remediation.py` | opt-in | `CONEXO_GATE_REMEDIATION_AUTO` desligado |
| Gate de valor M04.16D | opt-in | desligado |
| Publicação de comparativos | opt-in | desligado |
| `CONEXO_RSS_CRON_ACTIVE` | 0 | coleta manual |
| `CONEXO_ACTIONS_WRITER_DISABLED` | 1 | Actions writer desabilitado (política) |

## 3. SEO / GEO / AEO

| Item | Estado |
|---|---|
| Rank Math | ativo, 1.0.280 |
| Native SEO | ativo, 0.5.2, não assinado (falta chave) |
| Title da home | ❌ quebrado: `ConexoTech -` |
| Canonical / OG / Twitter / noindex | ✅ OK |
| Sitemaps | 5 no índice |
| Schema A57 | ❌ duplicação: Person×2, Rating×8, Review×21 |
| `llms.txt` | ✅ publicado (3.197 bytes) |
| GEO dashboard | parado em 04/10, scores 0 |
| Ferramentas GEO/AEO | scripts pontuais, nenhuma integrada ao fluxo |
| Regra 15 | AEO/GEO não é disciplina separada; `llms.txt` não muda Google |

## 4. Credenciais (somente nomes/estado — sem valores)

| Arquivo / origem | Estado |
|---|---|
| `wp-editorial.token` (24 chars) | conta Bot.editor, restrita a correção (403 em escrita) |
| `wp-engine.token` (24 chars) | conta Bot.editor, cria rascunhos (200), UUID `3a7fac3b…` |
| `wp-draft-writer.env` | criado, `600` |
| `cxrm_editor_app_password_uuid` | `6b060cb4…` (Conexo MKT-RSS) |
| `turso-readonly.token` / `turso-rss-writer.token` | válidos, expiram 20/11, permissão `rw` (API não gerou `ro`) |
| `rss-queue.env` | `CONEXO_ACTIONS_WRITER_DISABLED=1`, `CONEXO_RSS_CRON_ACTIVE=0`, `CONEXO_PRODUCT_LINKS_ENABLED=1` |
| `ai-keys.env` | GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, GEMINI_MODEL, OPENROUTER_MODEL, AI_FREE_ONLY_ALLOWLIST |
| `groq-editorial.token` | presente (56 bytes) |
| GitHub MKT-RSS | 13 secrets (Groq, Turso, WP, Unsplash, EXA, Jina, Sheets, Telegram) |
| GitHub site | 36 secrets, incluindo `YOUTUBE_API_KEY`, `WP_USER_ADMIN`, FTP/SFTP, Hostinger, Drive, Notion, OpenCode |
| `CONEXO_EDITORIAL_GATE_KEY` | **ausente** — SEO nativo assinado indisponível |

## 5. Rascunhos e pautas

| Item | Estado |
|---|---|
| Post 9899 (Senado) | lixeira |
| Post 9900 (Anatel/TIM) | draft, manifesto presente, capa 0, sem vídeo |
| Post 9906 (TV 65″) | draft, manifesto presente, capa 0, sem vídeo |
| Fila Turso | 22 em `DESCOBERTA`, 3 em `SELECIONADA` |
| 37 rascunhos antigos | fila de correção, imagem licenciada pendente |

## 6. Pendências abertas (não executadas)

- Vídeo review: módulo portado, mas sem chave no servidor e sem vídeo curado
- Capa: sem imagem com direito verificado
- Token Turso `ro`: não gerado pela API
- SEO nativo assinado: falta chave
- Opt-ins: remediação, gate de valor, comparativos
- Aceite humano no Gate: nenhum artigo aprovado/publicado

## Referência por tema

- SEO/GEO/AEO: `docs/REGRA15_NOTAS.md`, `docs/PENDENCIAS_2026-10-03.md`, `docs/CLOUD_EDITORIAL_20261109.md`
- Credenciais: `docs/CREDENCIAL_MOTOR_20261117.md`
- Mecanismo triagem: `docs/TRIAGE_MECANISMO_CHATGPT_VS_OPENCODE_20261117.md`
- Gargalo WordPress: `docs/GARGALO_RASCUNHO_WORDPRESS_20261117.md`
- Regeneração: `docs/REGENERACAO_MOTOR_20261117.md`
- Auditoria módulos: `docs/AUDITORIA_MODULOS_CREDENCIAIS_20261118.md`
- Pautas: `docs/PAUTAS_TRIAGEM_20261117.md`, `docs/PAUTAS_SELECIONADAS_20261117.md`
- M11 Binance: `docs/M11_FICHA_REVISAO_20261117.md`
- M14 preços: `docs/M14_AUDITORIA_PRECOS_20261117.md`
- M07 fila: `docs/M07_FILA_CORRECAO_20261117.md`
- M19 SEO: `docs/M19_INVENTARIO_SEO_20261117.md`
- Gate política: `docs/EDITORIAL-IMMEDIATE-PUBLICATION-POLICY-20261113.md`
- Vídeo: `docs/site/politica-curadoria-video.md`

<!-- registro-unico:auto:start -->

## Documentos de auditoria reconhecidos (atualizado automaticamente)

- `docs/AUDITORIA_MODULOS_CREDENCIAIS_20261118.md` — Auditoria de mÃ³dulos desligados e credenciais â€” 18/11/2026
- `docs/CREDENCIAL_MOTOR_20261117.md` — Credencial do motor editorial â€” 17/11/2026
- `docs/GARGALO_RASCUNHO_WORDPRESS_20261117.md` — Gargalo entre geraÃ§Ã£o e WordPress â€” diagnÃ³stico e soluÃ§Ã£o â€” 17/11/2026
- `docs/M07_FILA_CORRECAO_20261117.md` — M07 â€” Fila de correÃ§Ã£o de rascunhos â€” 17/11/2026
- `docs/M14_AUDITORIA_PRECOS_20261117.md` — M14 â€” Auditoria de preÃ§os publicados â€” 17/11/2026
- `docs/PAUTAS_SELECIONADAS_20261117.md` — Duas pautas escolhidas â€” briefing e conferÃªncia â€” 17/11/2026
- `docs/PAUTAS_TRIAGEM_20261117.md` — Pautas paradas na fila â€” triagem de 17/11/2026
- `docs/REGENERACAO_MOTOR_20261117.md` — RegeneraÃ§Ã£o dos dois artigos pelo motor â€” 17/11/2026
- `docs/TRIAGE_MECANISMO_CHATGPT_VS_OPENCODE_20261117.md` — Como a triagem era feita e como ficou no OpenCode â€” 17/11/2026

<!-- registro-unico:auto:end -->
