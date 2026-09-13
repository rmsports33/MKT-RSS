"""
admin/bot.py — Bot Telegram para aprovar rascunho pelo celular (esqueleto).

Fluxo: usuário manda /drafts → bot lista rascunhos → botões Aprovar/Recusar.
Aprovar chama wp_publisher para publish (só PASS). Sem custo além do hosting
(Railway/Render free dorme; melhor: VM sempre ligada ou GitHub Action com polling).

Uso:
  export TELEGRAM_BOT_TOKEN=...
  export WP_URL=... WP_USER=... WP_APP_PASSWORD=...
  python admin/bot.py

Requer: pip install python-telegram-bot==20.*
"""
import logging
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except Exception:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
WP_URL = os.getenv("WP_URL", "")
WP_USER = os.getenv("WP_USER", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")

HELP = (
    "Comandos:\n"
    "/drafts — lista rascunhos\n"
    "/health — checa WP e Groq\n"
    "/help — esta ajuda"
)

def _wp_list_drafts(limit: int = 5) -> list:
    """Lista rascunhos via WP REST (sem dependência extra)."""
    import requests, base64
    if not (WP_URL and WP_USER and WP_APP_PASSWORD):
        return []
    auth = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
    try:
        r = requests.get(f"{WP_URL.rstrip('/')}/wp-json/wp/v2/posts",
                         headers={"Authorization": f"Basic {auth}"},
                         params={"status": "draft", "per_page": limit}, timeout=15)
        r.raise_for_status()
        return [{"id": p.get("id"), "title": (p.get("title") or {}).get("rendered", "")[:60], "link": p.get("link", "")}
                for p in r.json()]
    except Exception as e:
        logger.warning(f"WP list drafts falhou: {e}")
        return [{"id": 0, "title": f"erro: {str(e)[:80]}", "link": ""}]

def _wp_publish(post_id: int) -> dict:
    import requests, base64
    auth = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
    try:
        r = requests.post(f"{WP_URL.rstrip('/')}/wp-json/wp/v2/posts/{post_id}",
                          headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
                          json={"status": "publish"}, timeout=15)
        if r.status_code in (200, 201):
            return {"ok": True, "link": r.json().get("link", "")}
        return {"ok": False, "erro": f"WP {r.status_code}: {r.text[:100]}"}
    except Exception as e:
        return {"ok": False, "erro": str(e)[:120]}

# Handlers (python-telegram-bot v20)
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"ConexoTech Admin\n{HELP}")

    async def cmd_drafts(update: Update, context: ContextTypes.DEFAULT_TYPE):
        drafts = _wp_list_drafts()
        if not drafts:
            await update.message.reply_text("Nenhum rascunho ou WP não configurado.")
            return
        for d in drafts:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Publicar", callback_data=f"pub:{d['id']}"),
                                        InlineKeyboardButton("🔗 Ver", url=d["link"])]] if d["link"] else [])
            await update.message.reply_text(f"#{d['id']} — {d['title']}", reply_markup=kb)

    async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        await q.answer()
        data = q.data or ""
        if data.startswith("pub:"):
            pid = int(data.split(":")[1])
            res = _wp_publish(pid)
            await q.edit_message_text(f"{'✅ Publicado' if res.get('ok') else '❌ Falhou'}: {res.get('link') or res.get('erro', '')}")

    def main():
        if not TOKEN:
            print("TELEGRAM_BOT_TOKEN ausente — defina no .env ou Secrets")
            return
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("help", cmd_start))
        app.add_handler(CommandHandler("drafts", cmd_drafts))
        app.add_handler(CommandHandler("health", cmd_start))
        app.add_handler(CallbackQueryHandler(on_callback))
        print("Bot rodando — envie /drafts no Telegram")
        app.run_polling()

    if __name__ == "__main__":
        main()

except ImportError:
    # Sem lib instalada — não quebra o projeto, só não roda o bot
    def main():
        print("python-telegram-bot não instalado — pip install python-telegram-bot==20.*")

    if __name__ == "__main__":
        main()
