# Admin multi-plataforma — sem PC

Você já tem o pipeline na nuvem; faltava aprovar sem notebook.

## Opção A — Streamlit (recomendada, 5 min, grátis)

1. Conta em `share.streamlit.io` → New app → repo `rmsports33/MKT-RSS`, file `admin/app.py`.
2. Secrets do app: copie do seu `.env` → `WP_URL`, `WP_USER`, `WP_APP_PASSWORD`, `GROQ_API_KEY`.
3. Deploy. Abra no celular, adicione à tela inicial (vira app).
4. Uso: veja RSS do dia e custo, toque em "Ver rascunhos no WP" ou rode 1 dry-run.

Local: `streamlit run admin/app.py` (precisa `pip install streamlit`).

## Opção B — Telegram (aprova com 1 toque)

1. No Telegram, fale com `@BotFather` → `/newbot` → nome `conexotech_admin` → copie o token.
2. No `.env` (ou Secrets do host), defina `TELEGRAM_BOT_TOKEN` + `WP_*`.
3. Hospede `admin/bot.py` onde fique ligado (Railway free dorme — prefira VM ou Action com `run: python admin/bot.py`).
4. No chat do bot: `/drafts` → lista rascunhos com botão **Publicar**.

Ambos usam as mesmas chaves do projeto. Sem custo além do hosting do bot (free com ressalvas).
