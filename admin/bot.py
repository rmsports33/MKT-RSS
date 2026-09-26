"""
admin/bot.py — Bot Telegram para aprovar rascunho pelo celular (hardened).

Fluxo: /drafts → lista rascunhos → botão Publicar → POST /wp-json/wp/v2/posts/{id} publish.
Hardening: TELEGRAM_ALLOWED_IDS whitelist, /health real, callback auth, logs audit.

Uso:
  export TELEGRAM_BOT_TOKEN=... TELEGRAM_ALLOWED_IDS=123456,789012
  export WP_URL=... WP_USER=... WP_APP_PASSWORD=... GROQ_API_KEY=...
  python admin/bot.py

Host always-on (prod): não use polling efêmero no PC.
  Opções: Fly.io/Render (Dockerfile em admin/), ou polling via GitHub Action
  .github/workflows/bot.yml (keepalive 5min). Ver docs/ADMIN_MULTI.md.

Requer: pip install python-telegram-bot==20.* requests
"""
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN", "") or "").strip()
WP_URL = (os.getenv("WP_URL", "") or "").strip()
WP_USER = (os.getenv("WP_USER", "") or "").strip()
WP_APP_PASSWORD = (os.getenv("WP_APP_PASSWORD", "") or "").strip()
GROQ_KEY = (os.getenv("GROQ_API_KEY", "") or "").strip()

# --- Auth: whitelist de IDs (hardening crítico) ---
_raw_allowed = (os.getenv("TELEGRAM_ALLOWED_IDS", "") or "").strip()
ALLOWED_IDS: set[int] = set()
if _raw_allowed:
    for _p in _raw_allowed.split(","):
        _p = _p.strip()
        if _p.lstrip("-").isdigit():
            try:
                ALLOWED_IDS.add(int(_p))
            except Exception:
                pass

def _is_allowed(update) -> bool:
    """True se ALLOWED_IDS vazio (open, com aviso) ou user/chat in whitelist."""
    if not ALLOWED_IDS:
        logger.warning("TELEGRAM_ALLOWED_IDS vazio — bot aberto a qualquer chat (defina IDs em .env para travar)")
        return True
    try:
        uid = getattr(getattr(update, "effective_user", None), "id", None)
        cid = getattr(getattr(update, "effective_chat", None), "id", None)
        return (uid in ALLOWED_IDS) or (cid in ALLOWED_IDS)
    except Exception:
        return False

HELP = (
    "Comandos:\n"
    "/drafts [N] — lista rascunhos (default 5)\n"
    "/link <url> — registra link de afiliado (guiado por botoes)\n"
    "/cancelar — aborta o /link atual\n"
    "/health — checa WP e Groq (+ Turso se configurado)\n"
    "/help — esta ajuda\n\n"
    "Dica: defina TELEGRAM_ALLOWED_IDS=123456,789012 no .env para travar."
)

def _wp_list_drafts(limit: int = 5) -> list:
    """Lista rascunhos via WP REST (sem dependência extra)."""
    import requests, base64
    if not (WP_URL and WP_USER and WP_APP_PASSWORD):
        return []
    auth = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
    url = f"{WP_URL.rstrip('/')}/wp-json/wp/v2/posts"
    try:
        for params in ({"status": "draft", "per_page": limit, "context": "edit"},
                       {"status": "draft", "per_page": limit}):
            r = requests.get(url, headers={"Authorization": f"Basic {auth}"},
                             params=params, timeout=15)
            if r.status_code == 200:
                return [{"id": p.get("id"), "title": (p.get("title") or {}).get("rendered", "")[:60], "link": p.get("link", "")}
                        for p in r.json()]
            logger.warning(f"WP list drafts tentativa {params} -> HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        logger.warning(f"WP list drafts falhou: {e}")
        return [{"id": 0, "title": f"erro: {str(e)[:80]}", "link": ""}]
    return [{"id": 0, "title": "erro: WP retornou erro ao listar drafts (ver log)", "link": ""}]

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

    async def _guard(update: Update) -> bool:
        if not _is_allowed(update):
            try:
                uid = getattr(getattr(update, "effective_user", None), "id", "?")
                logger.warning(f"Acesso negado Telegram id={uid}")
                if getattr(update, "message", None):
                    await update.message.reply_text("⛔ Não autorizado. Seu ID não está em TELEGRAM_ALLOWED_IDS.")
                elif getattr(update, "callback_query", None):
                    await update.callback_query.answer("⛔ Não autorizado", show_alert=True)
            except Exception:
                pass
            return False
        return True

    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await _guard(update):
            return
        await update.message.reply_text(f"ConexoTech Admin\n{HELP}")

    async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await _guard(update):
            return
        linhas = []
        # WP
        if not (WP_URL and WP_USER and WP_APP_PASSWORD):
            linhas.append("WP: ❌ WP_URL/USER/APP_PASSWORD ausentes")
        else:
            try:
                import requests
                r = requests.get(f"{WP_URL.rstrip('/')}/wp-json/", timeout=8, headers={"User-Agent": "Mozilla/5.0"})
                linhas.append(f"WP: {'✅' if r.status_code==200 else '❌'} {WP_URL} HTTP {r.status_code}")
            except Exception as e:
                linhas.append(f"WP: ❌ {str(e)[:80]}")
        # Groq
        linhas.append(f"Groq: {'✅' if GROQ_KEY else '❌ sem GROQ_API_KEY'}")
        # Turso
        try:
            from mkt_flow_p0.cloud_db import turso_enabled
            linhas.append(f"Turso: {'✅ nuvem' if turso_enabled() else '⚠️ local SQLite (defina TURSO_* p/ dedup entre dias)'}")
        except Exception as e:
            linhas.append(f"Turso: ? {str(e)[:60]}")
        # drafts count
        drafts = _wp_list_drafts(limit=1)
        if drafts and drafts[0].get("id", 0) != 0:
            linhas.append(f"Drafts: {len(_wp_list_drafts(limit=5))} rascunhos")
        await update.message.reply_text("\n".join(linhas))

    async def cmd_drafts(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await _guard(update):
            return
        # parse /drafts 7
        limit = 5
        try:
            if context.args:
                limit = max(1, min(10, int(context.args[0])))
        except Exception:
            pass
        drafts = _wp_list_drafts(limit=limit)
        if not drafts or (len(drafts)==1 and drafts[0].get("id")==0 and "erro" in drafts[0].get("title","")):
            await update.message.reply_text(f"Nenhum rascunho ou WP erro: {drafts[0].get('title','') if drafts else 'WP não configurado'}")
            return
        if not drafts:
            await update.message.reply_text("Nenhum rascunho.")
            return
        for d in drafts:
            try:
                pid = int(d.get("id") or 0)
                if pid == 0:
                    await update.message.reply_text(d.get("title",""))
                    continue
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Publicar", callback_data=f"pub:{pid}"),
                                            InlineKeyboardButton("🔗 Ver", url=d["link"])]] if d.get("link") else
                                          [[InlineKeyboardButton("✅ Publicar", callback_data=f"pub:{pid}")]])
                await update.message.reply_text(f"#{pid} — {d['title']}", reply_markup=kb)
            except Exception as e:
                logger.warning(f"draft send falhou: {e}")

    async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await _guard(update):
            return
        q = update.callback_query
        try:
            await q.answer()
        except Exception:
            pass
        data = q.data or ""
        if data.startswith("pub:"):
            try:
                pid = int(data.split(":")[1])
            except Exception:
                await q.edit_message_text("ID inválido")
                return
            res = _wp_publish(pid)
            # log audit
            try:
                uid = getattr(getattr(update, "effective_user", None), "id", "?")
                logger.info(f"Telegram publish pid={pid} por {uid} -> {res}")
            except Exception:
                pass
            await q.edit_message_text(f"{'✅ Publicado' if res.get('ok') else '❌ Falhou'}: {res.get('link') or res.get('erro', '')}")

    async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Diagnostico claro de conflito 409 (duas instancias com o mesmo token)."""
        err = getattr(context, "error", None)
        msg = str(err)
        if ("onflict" in type(err).__name__
                or "terminated by other getUpdates" in msg
                or " 409" in msg or msg.startswith("409")):
            logger.error(
                "CONFLITO 409: outra instancia do bot esta rodando com este token! "
                "Solucao: Fly.io = 1 machine, nada rodando local, nenhum workflow paralelo. "
                "Depois, reinicie esta instancia.")
        else:
            logger.warning(f"Erro no bot: {msg[:200]}")

    def main():
        if not TOKEN:
            print("TELEGRAM_BOT_TOKEN ausente — defina no .env ou Secrets (e TELEGRAM_ALLOWED_IDS para travar)")
            return
        if not ALLOWED_IDS:
            print("AVISO: TELEGRAM_ALLOWED_IDS vazio — bot aceitará qualquer chat. Defina IDs para prod.")
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("help", cmd_start))
        app.add_handler(CommandHandler("drafts", cmd_drafts))
        app.add_handler(CommandHandler("health", cmd_health))
        app.add_handler(CallbackQueryHandler(on_callback))
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            import linkflow
            h = linkflow.link_conv_handler()
            if h is not None:
                app.add_handler(h)
                logger.info("handler /link registrado")
            else:
                logger.warning("/link indisponivel (sem python-telegram-bot no import do linkflow)")
        except Exception as e:
            logger.warning(f"/link nao registrado: {e}")
        app.add_error_handler(on_error)
        print(f"Bot rodando — envie /drafts no Telegram (allowlist: {ALLOWED_IDS or 'aberta'})")
        # polling com drop_pending e timeout explícito (host always-on: ver docs/ADMIN_MULTI.md)
        app.run_polling(drop_pending_updates=True, allowed_updates=["message","callback_query"])

    if __name__ == "__main__":
        main()

except ImportError:
    # Sem lib instalada — não quebra o projeto, só não roda o bot
    def main():
        print("python-telegram-bot não instalado — pip install python-telegram-bot==20.*")

    if __name__ == "__main__":
        main()
