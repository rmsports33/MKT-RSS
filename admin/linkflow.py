"""
admin/linkflow.py — /link: registra link de afiliado na aba
"Links pendentes (5 guias)" da planilha-mestre, guiado por botoes.

Fluxo (decidido com o dono em 26/09/2026):
  /link <url> -> [escolhe guia] -> [escolhe produto] -> [escolhe loja]
  -> celula vazia: grava e confirma
  -> celula ocupada: mostra o link antigo + [Trocar] [Manter]

Regras:
- Nunca roda polling aqui: handlers sao registrados pelo admin/bot.py
  (que roda no Fly.io). Rodar 2 instancias com o mesmo token = conflito 409.
- Escrita no Sheets so na celula produto x loja, valueInputOption=RAW,
  com releitura de confirmacao. Sem --aplicar aqui: o /link E a aplicacao.
- Import do python-telegram-bot e opcional: sem a lib, o modulo importa
  (funcoes puras + Sheets testaveis) mas link_conv_handler() retorna None.

Destino:
  SID = 1D3t7YCMT_hea_Gd9kI-Iknuzmp1mzI7u3vDIozvfj_0
  ABA = "Links pendentes (5 guias)" | Cols: A=Produto B=Shopee C=ML D=KaBuM! E=Amazon F=Magalu G=Obs
"""
import json
import logging
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:
    pass

logger = logging.getLogger("linkflow")

SID = "1D3t7YCMT_hea_Gd9kI-Iknuzmp1mzI7u3vDIozvfj_0"
ABA = "Links pendentes (5 guias)"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

GUIAS = {
    "smartwatch": ("Smartwatch", [
        "Galaxy Watch Ultra 2",
        "Galaxy Watch 9 40mm Wi-Fi",
        "Galaxy Watch 9 44mm Wi-Fi",
    ]),
    "tv4k": ("TV 4K", [
        "Samsung S90F 55",
        "TCL P7K 55",
        "LG QNED85 55",
        "TCL C6K 55",
        "Samsung QN90F 55",
        "Samsung S85F 55",
        "LG OLED C5 55",
    ]),
    "notebook": ("Notebook", [
        "Asus Vivobook Go 15",
        "Lenovo IdeaPad Slim 3",
    ]),
    "caixa_som": ("Caixa de som", [
        "Tribit Stormbox Blast 1",
        "Tribit Stormbox Blast 2",
    ]),
    "teclado": ("Teclado", [
        "Keychron V6 Max",
    ]),
}
LOJAS = ["Shopee", "Mercado Livre", "KaBuM!", "Amazon", "Magazine Luiza"]
COL = {loja: c for loja, c in zip(LOJAS, "BCDEF")}

LINK_HELP = "/link <url> — registra link de afiliado (guiado por botoes)\n/cancelar — aborta o /link atual"

USO = ("Uso: /link <url>\n"
       "Exemplo: /link https://www.amazon.com.br/dp/B0XXXXXXX\n"
       "Depois e so tocar nos botoes: guia -> produto -> loja.")


# ---------------------------------------------------------------- puras
def norm_url(txt):
    """Normaliza URL colada. Devolve URL ou None (invalida)."""
    t = (txt or "").strip().strip("<>").strip()
    if not t or " " in t or "\n" in t:
        return None
    if "://" not in t:
        if "." not in t:
            return None
        t = "https://" + t
    try:
        p = urlparse(t)
    except Exception:
        return None
    if p.scheme not in ("http", "https"):
        return None
    if not p.netloc or "." not in p.netloc:
        return None
    return t


def checa_url_viva(url, timeout=10):
    """GET leve com UA de navegador. (ok, detalhe). Nao-bloqueante: loja pode
    dar 403 a robo — quem decide e o dono na confirmacao."""
    import requests
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout,
                         allow_redirects=True)
        if r.status_code < 400:
            return True, "HTTP %s ✅" % r.status_code
        return False, "HTTP %s ⚠️ (loja bloqueou o teste; o link pode estar ok)" % r.status_code
    except Exception as e:
        return False, "sem resposta (%s) ⚠️" % str(e)[:60]


def todos_produtos():
    return [p for _g, (_rot, ps) in GUIAS.items() for p in ps]


# ---------------------------------------------------------------- Sheets
def _creds():
    """Service account: env GOOGLE_SHEETS_JSON (conteudo JSON, p/ Fly.io)
    ou arquivo (local)."""
    from google.oauth2.service_account import Credentials
    raw = (os.getenv("GOOGLE_SHEETS_JSON", "") or "").strip()
    if raw.startswith("{"):
        return Credentials.from_service_account_info(json.loads(raw), scopes=SCOPES)
    p = Path(raw) if raw else None
    if not p or not p.exists():
        p = Path.home() / ".conexotech" / "secrets" / "google-sheets.json"
    if not p.exists():
        raise RuntimeError("credencial Sheets ausente (GOOGLE_SHEETS_JSON ou ~/.conexotech/secrets/google-sheets.json)")
    return Credentials.from_service_account_file(str(p), scopes=SCOPES)


def _service():
    from googleapiclient.discovery import build
    return build("sheets", "v4", credentials=_creds())


def mapa_produto_linha(svc=None):
    """{produto: n_linha} lendo a coluna A da aba. Prova de endereco real."""
    svc = svc or _service()
    vals = svc.spreadsheets().values().get(
        spreadsheetId=SID, range="'%s'!A:A" % ABA).execute().get("values", [])
    out = {}
    for i, r in enumerate(vals[1:], start=2):
        if r and r[0].strip():
            out[r[0].strip()] = i
    return out


def le_celula(produto, loja, svc=None):
    svc = svc or _service()
    mapa = mapa_produto_linha(svc)
    if produto not in mapa:
        raise ValueError("produto fora da aba: %s" % produto)
    if loja not in COL:
        raise ValueError("loja invalida: %s" % loja)
    rng = "'%s'!%s%d" % (ABA, COL[loja], mapa[produto])
    vals = svc.spreadsheets().values().get(spreadsheetId=SID, range=rng).execute().get("values", [])
    return (vals[0][0] if vals and vals[0] else "").strip()


def grava_link(produto, loja, url, svc=None):
    """Grava URL na celula produto x loja e rele para confirmar.
    Devolve (ok, valor_lido)."""
    svc = svc or _service()
    mapa = mapa_produto_linha(svc)
    if produto not in mapa:
        raise ValueError("produto fora da aba: %s" % produto)
    if loja not in COL:
        raise ValueError("loja invalida: %s" % loja)
    rng = "'%s'!%s%d" % (ABA, COL[loja], mapa[produto])
    svc.spreadsheets().values().update(
        spreadsheetId=SID, range=rng, valueInputOption="RAW",
        body={"values": [[url]]}).execute()
    lido = le_celula(produto, loja, svc)
    return (lido == url, lido)


# ---------------------------------------------------------------- Telegram (opcional)
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                              ConversationHandler, ContextTypes, MessageHandler, filters)
    _TEM_PTB = True
except ImportError:
    _TEM_PTB = False

if _TEM_PTB:
    ST_GUIA, ST_PROD, ST_LOJA, ST_TROCA = range(4)

    def _permitido(update) -> bool:
        raw = (os.getenv("TELEGRAM_ALLOWED_IDS", "") or "").strip()
        if not raw:
            return True
        ids = set()
        for p in raw.split(","):
            p = p.strip()
            if p.lstrip("-").isdigit():
                ids.add(int(p))
        uid = getattr(getattr(update, "effective_user", None), "id", None)
        cid = getattr(getattr(update, "effective_chat", None), "id", None)
        return (uid in ids) or (cid in ids)

    async def _negado(update):
        try:
            if getattr(update, "message", None):
                await update.message.reply_text("⛔ Não autorizado.")
            elif getattr(update, "callback_query", None):
                await update.callback_query.answer("⛔ Não autorizado", show_alert=True)
        except Exception:
            pass

    def _kb_guias():
        fileiras = [[InlineKeyboardButton("⌚ Smartwatch", callback_data="lk:g:smartwatch")],
                    [InlineKeyboardButton("📺 TV 4K", callback_data="lk:g:tv4k")],
                    [InlineKeyboardButton("💻 Notebook", callback_data="lk:g:notebook")],
                    [InlineKeyboardButton("🔊 Caixa de som", callback_data="lk:g:caixa_som")],
                    [InlineKeyboardButton("⌨️ Teclado", callback_data="lk:g:teclado")]]
        return InlineKeyboardMarkup(fileiras)

    def _kb_produtos(guia):
        _rot, prods = GUIAS[guia]
        fileiras = [[InlineKeyboardButton(p, callback_data="lk:p:%d" % i)] for i, p in enumerate(prods)]
        fileiras.append([InlineKeyboardButton("⬅️ Voltar", callback_data="lk:voltar_guias")])
        return InlineKeyboardMarkup(fileiras)

    def _kb_lojas():
        fileiras = [[InlineKeyboardButton("🏪 " + l, callback_data="lk:l:" + l)] for l in LOJAS]
        fileiras.append([InlineKeyboardButton("⬅️ Voltar", callback_data="lk:voltar_prods")])
        return InlineKeyboardMarkup(fileiras)

    def _limpa(d):
        for k in ("lk_url", "lk_guia", "lk_prod", "lk_loja"):
            d.pop(k, None)

    async def cmd_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _permitido(update):
            await _negado(update)
            return ConversationHandler.END
        url = norm_url(" ".join(context.args or []))
        if not url:
            await update.message.reply_text(USO)
            return ConversationHandler.END
        context.user_data["lk_url"] = url
        ok, detalhe = checa_url_viva(url)
        await update.message.reply_text(
            "🔗 %s\n%s\n\nQual guia?" % (url, detalhe), reply_markup=_kb_guias(),
            disable_web_page_preview=True)
        return ST_GUIA

    async def on_guia(update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        try:
            await q.answer()
        except Exception:
            pass
        if not _permitido(update):
            await _negado(update)
            return ConversationHandler.END
        guia = (q.data or "").split(":")[-1]
        if guia not in GUIAS:
            await q.edit_message_text("Guia inválido. /link para recomeçar.")
            return ConversationHandler.END
        context.user_data["lk_guia"] = guia
        await q.edit_message_text("Guia: %s\n\nQual produto?" % GUIAS[guia][0],
                                  reply_markup=_kb_produtos(guia))
        return ST_PROD

    async def on_voltar(update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        try:
            await q.answer()
        except Exception:
            pass
        if not _permitido(update):
            await _negado(update)
            return ConversationHandler.END
        if (q.data or "").endswith("guias"):
            await q.edit_message_text("Qual guia?", reply_markup=_kb_guias())
            return ST_GUIA
        guia = context.user_data.get("lk_guia")
        if guia not in GUIAS:
            await q.edit_message_text("Qual guia?", reply_markup=_kb_guias())
            return ST_GUIA
        await q.edit_message_text("Guia: %s\n\nQual produto?" % GUIAS[guia][0],
                                  reply_markup=_kb_produtos(guia))
        return ST_PROD

    async def on_prod(update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        try:
            await q.answer()
        except Exception:
            pass
        if not _permitido(update):
            await _negado(update)
            return ConversationHandler.END
        guia = context.user_data.get("lk_guia")
        try:
            idx = int((q.data or "").split(":")[-1])
            prod = GUIAS[guia][1][idx]
        except Exception:
            await q.edit_message_text("Produto inválido. /link para recomeçar.")
            return ConversationHandler.END
        context.user_data["lk_prod"] = prod
        await q.edit_message_text("Produto: %s\n\nQual loja?" % prod, reply_markup=_kb_lojas())
        return ST_LOJA

    async def on_loja(update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        try:
            await q.answer()
        except Exception:
            pass
        if not _permitido(update):
            await _negado(update)
            return ConversationHandler.END
        loja = (q.data or "").split(":", 2)[-1]
        if loja not in LOJAS:
            await q.edit_message_text("Loja inválida. /link para recomeçar.")
            return ConversationHandler.END
        context.user_data["lk_loja"] = loja
        prod = context.user_data.get("lk_prod")
        url = context.user_data.get("lk_url")
        try:
            atual = le_celula(prod, loja)
        except Exception as e:
            logger.warning("le_celula falhou: %s", e)
            await q.edit_message_text("❌ Erro ao ler a planilha: %s" % str(e)[:100])
            return ConversationHandler.END
        if not atual:
            try:
                ok, lido = grava_link(prod, loja, url)
            except Exception as e:
                logger.warning("grava_link falhou: %s", e)
                await q.edit_message_text("❌ Erro ao gravar: %s" % str(e)[:100])
                return ConversationHandler.END
            _limpa(context.user_data)
            await q.edit_message_text(
                "✅ Gravado: %s | %s\n%s" % (prod, loja, lido) if ok
                else "⚠️ Gravado mas a releitura divergiu — confira na planilha.",
                disable_web_page_preview=True)
            return ConversationHandler.END
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Trocar", callback_data="lk:trocar"),
                                    InlineKeyboardButton("✔️ Manter", callback_data="lk:manter")]])
        await q.edit_message_text(
            "⚠️ Já existe link para %s | %s:\n%s\n\nTrocar pelo novo?\n%s"
            % (prod, loja, atual, url), reply_markup=kb, disable_web_page_preview=True)
        return ST_TROCA

    async def on_troca(update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        try:
            await q.answer()
        except Exception:
            pass
        if not _permitido(update):
            await _negado(update)
            return ConversationHandler.END
        acao = (q.data or "").split(":")[-1]
        prod = context.user_data.get("lk_prod")
        loja = context.user_data.get("lk_loja")
        url = context.user_data.get("lk_url")
        if acao == "manter":
            _limpa(context.user_data)
            await q.edit_message_text("✔️ Mantido o link antigo. Nada alterado.")
            return ConversationHandler.END
        try:
            ok, lido = grava_link(prod, loja, url)
        except Exception as e:
            await q.edit_message_text("❌ Erro ao gravar: %s" % str(e)[:100])
            return ConversationHandler.END
        _limpa(context.user_data)
        await q.edit_message_text("✅ Trocado: %s | %s\n%s" % (prod, loja, lido)
                                  if ok else "⚠️ Troca sem confirmação de releitura.",
                                  disable_web_page_preview=True)
        return ConversationHandler.END

    async def cmd_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
        _limpa(context.user_data)
        try:
            await update.message.reply_text("Cancelado. /link para recomeçar.")
        except Exception:
            pass
        return ConversationHandler.END

    def link_conv_handler():
        return ConversationHandler(
            entry_points=[CommandHandler("link", cmd_link)],
            states={
                ST_GUIA: [CallbackQueryHandler(on_guia, pattern=r"^lk:g:")],
                ST_PROD: [CallbackQueryHandler(on_prod, pattern=r"^lk:p:"),
                          CallbackQueryHandler(on_voltar, pattern=r"^lk:voltar_guias$")],
                ST_LOJA: [CallbackQueryHandler(on_loja, pattern=r"^lk:l:"),
                          CallbackQueryHandler(on_voltar, pattern=r"^lk:voltar_prods$")],
                ST_TROCA: [CallbackQueryHandler(on_troca, pattern=r"^lk:(trocar|manter)$")],
            },
            fallbacks=[CommandHandler("cancelar", cmd_cancelar)],
            per_chat=True,
        )
else:
    def link_conv_handler():
        return None
