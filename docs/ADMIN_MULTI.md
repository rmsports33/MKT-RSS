# Admin multi-plataforma — sem PC (hardened)

Você já tem o pipeline na nuvem; faltava aprovar sem notebook.

## Opção A — Streamlit (recomendada, 5 min, grátis)

1. Conta em `share.streamlit.io` → New app → repo `rmsports33/MKT-RSS`, file `admin/app.py`.
2. Secrets do app (Settings → Secrets): `WP_URL`, `WP_USER`, `WP_APP_PASSWORD`, `GROQ_API_KEY`, `GROQ_MODEL`, `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN` — copie do `.env.example` (hardening `admin/app.py:30` fix `_get_secret` lê env→secrets sem precedência bugada).
3. Deploy. Abra no celular, adicione à tela inicial (vira app).
4. Uso: Dashboard `rss_total/publicados/custo` + `Fonte RSS` selectbox (feed param, não hardcode) + `Feed custom/URL direta` expander + botão `Rodar pipeline RSS (fonte, N itens, dry-run)`.

Local: `streamlit run admin/app.py` (precisa `pip install streamlit feedparser trafilatura`).

## Opção B — Telegram (aprova com 1 toque, hardened)

**Auth obrigatória em prod:** `TELEGRAM_ALLOWED_IDS`

1. No Telegram, `@BotFather` → `/newbot` → `conexotech_admin` → token.
2. Descubra seu ID: envie `/start` ao `@userinfobot` ou rode bot e veja log `Acesso negado id=...`. Copie.
3. No `.env` / host Secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_IDS=123456,789012`, `WP_*`, `GROQ_API_KEY`.
4. Comandos: `/drafts [N]` (1-10), `/health` (WP/Groq/Turso), `/help`. Callback `Publicar` agora checa whitelist e loga `uid`.

**Host always-on (não deixe no PC):**

| Host | Como | Custo |
|---|---|---|
| **Fly.io (recomendado)** | `fly launch --dockerfile admin/Dockerfile` → `fly secrets set TELEGRAM_BOT_TOKEN=... TELEGRAM_ALLOWED_IDS=... WP_*` | free tier 3 VMs |
| **Render** | New Web Service → Dockerfile `admin/Dockerfile` → env vars | free dorme se sem ping — use `cron-job.org` ping |
| ~~**GitHub Actions (fallback)**~~ | ❌ **REMOVIDO em 14/09/2026 (commit 5853ab2): causava conflito 409 com o Fly.io — NÃO recriar** | — |
| **VM própria** | `systemd` + `python admin/bot.py` | |

> Sem `TELEGRAM_ALLOWED_IDS`, bot fica aberto (log `AVISO: allowlist aberta`). Defina antes de ir a prod.

Ambos usam mesmas chaves. Feed param e `st.secrets` fix validados em `admin/app.py:30`.
