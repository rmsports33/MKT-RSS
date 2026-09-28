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
import re
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
# SEM MEMORIA: cada rodada do bot e um processo novo, entao nada de estado em
# memoria. O estado viaja no callback_data e o link no texto da mensagem.
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                              ContextTypes, MessageHandler, filters)
    _TEM_PTB = True
except ImportError:
    _TEM_PTB = False

# callback_data (curto, sem acento):
#   lk:g:<guia>                         -> escolheu o guia
#   lk:p:<guia>:<idx>                   -> escolheu o produto
#   lk:l:<guia>:<idx>:<loja_idx>        -> escolheu a loja (grava ou pergunta troca)
#   lk:x:<guia>:<idx>:<loja_idx>:<0|1>  -> 0=manter antigo, 1=trocar
MAX_IDADE_H = 24


def url_da_mensagem(texto):
    """Recupera o link do texto da mensagem (prefixo 🔗). Puro e testavel."""
    m = re.search(r"🔗\s*(https?://\S+)", texto or "")
    return m.group(1) if m else None


def _expirou(data_msg, max_horas=MAX_IDADE_H, agora=None):
    """True se a mensagem/botao e velho demais (o dono ta madrugada afora)."""
    if data_msg is None:
        return False
    from datetime import datetime, timedelta, timezone
    ref = agora or datetime.now(timezone.utc)
    if data_msg.tzinfo is None:
        data_msg = data_msg.replace(tzinfo=timezone.utc)
    return (ref - data_msg) > timedelta(hours=max_horas)


if _TEM_PTB:
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
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("⌚ Smartwatch", callback_data="lk:g:smartwatch")],
            [InlineKeyboardButton("📺 TV 4K", callback_data="lk:g:tv4k")],
            [InlineKeyboardButton("💻 Notebook", callback_data="lk:g:notebook")],
            [InlineKeyboardButton("🔊 Caixa de som", callback_data="lk:g:caixa_som")],
            [InlineKeyboardButton("⌨️ Teclado", callback_data="lk:g:teclado")],
        ])

    def _kb_produtos(guia):
        _rot, prods = GUIAS[guia]
        linhas = [[InlineKeyboardButton(p, callback_data="lk:p:%s:%d" % (guia, i))]
                  for i, p in enumerate(prods)]
        linhas.append([InlineKeyboardButton("⬅️ Trocar o guia",
                                            callback_data="lk:g:__volta__")])
        return InlineKeyboardMarkup(linhas)

    def _kb_lojas(guia, idx):
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("%d. %s" % (i + 1, l),
                                    callback_data="lk:l:%s:%d:%d" % (guia, idx, i))]
             for i, l in enumerate(LOJAS)]
            + [[InlineKeyboardButton("⬅️ Trocar o produto",
                                     callback_data="lk:p:%s:%d:__volta__" % (guia, idx))]])

    def _kb_troca(guia, idx, loja_idx):
        base = "lk:x:%s:%d:%d:" % (guia, idx, loja_idx)
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("🔁 Trocar", callback_data=base + "1"),
            InlineKeyboardButton("✔️ Manter o antigo", callback_data=base + "0"),
        ]])

    async def cmd_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _permitido(update):
            await _negado(update)
            return
        url = norm_url(" ".join(context.args or []))
        if not url:
            await update.message.reply_text(USO)
            return
        ok, detalhe = checa_url_viva(url)
        logger.info("/link recebido de uid=%s: %s (%s)", getattr(getattr(update, "effective_user", None), "id", "?"), url[:80], detalhe[:40])
        await update.message.reply_text(
            "🔗 %s\n%s\n\nQual guia?" % (url, detalhe), reply_markup=_kb_guias(),
            disable_web_page_preview=True)

    async def on_lk(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unico handler de botoes do /link. Stateless."""
        q = update.callback_query
        try:
            await q.answer()
        except Exception:
            pass
        if not _permitido(update):
            await _negado(update)
            return
        partes = (q.data or "").split(":")
        logger.info("botao recebido: %s (de %d partes)", q.data, len(partes))
        if len(partes) < 3 or partes[0] != "lk":
            return
        msg = getattr(q, "message", None)
        url = url_da_mensagem(getattr(msg, "text", "") or "")
        if not url:
            await q.edit_message_text(
                "⚠️ Não encontrei o link nesta mensagem. Mande /link <url> de novo.")
            return
        if _expirou(getattr(msg, "date", None)):
            await q.edit_message_text(
                "⏳ Esse botão é de mais de %dh. Mande /link <url> de novo." % MAX_IDADE_H,
                reply_markup=None)
            return

        acao = partes[1]

        if acao == "g":
            guia = partes[2]
            if guia == "__volta__":
                await q.edit_message_text("🔗 %s\n\nQual guia?" % url, reply_markup=_kb_guias())
                return
            if guia not in GUIAS:
                await q.edit_message_text("Guia inválido. Mande /link <url> de novo.")
                return
            await q.edit_message_text(
                "🔗 %s\nGuia: %s\n\nQual produto?" % (url, GUIAS[guia][0]),
                reply_markup=_kb_produtos(guia))
            return

        guia = partes[2]

        if acao == "p":
            if len(partes) >= 4 and partes[3] == "__volta__":
                await q.edit_message_text("🔗 %s\n\nQual guia?" % url, reply_markup=_kb_guias())
                return
            try:
                idx = int(partes[3])
                prod = GUIAS[guia][1][idx]
            except Exception:
                await q.edit_message_text("Produto inválido. Mande /link <url> de novo.")
                return
            await q.edit_message_text(
                "🔗 %s\nProduto: %s\n\nQual loja?" % (url, prod),
                reply_markup=_kb_lojas(guia, idx))
            return

        if guia not in GUIAS:
            await q.edit_message_text("Guia inválido. Mande /link <url> de novo.")
            return
        try:
            idx = int(partes[3])
            prod = GUIAS[guia][1][idx]
        except Exception:
            await q.edit_message_text("Produto inválido. Mande /link <url> de novo.")
            return

        if acao == "l":
            try:
                loja = LOJAS[int(partes[4])]
            except Exception:
                await q.edit_message_text("Loja inválido. Mande /link <url> de novo.")
                return
            try:
                atual = le_celula(prod, loja)
            except Exception as e:
                await q.edit_message_text("❌ Erro ao ler a planilha: %s" % str(e)[:120])
                return
            if not atual:
                try:
                    ok, lido = grava_link(prod, loja, url)
                except Exception as e:
                    await q.edit_message_text("❌ Erro ao gravar: %s" % str(e)[:120])
                    return
                await q.edit_message_text(
                    ("✅ Gravado!\n%s | %s\n%s" % (prod, loja, lido)) if ok
                    else "⚠️ Gravado, mas a releitura divergiu — confira na planilha.")
                return
            await q.edit_message_text(
                "⚠️ Já existe link para %s | %s:\n%s\n\nTrocar pelo novo?"
                % (prod, loja, atual), reply_markup=_kb_troca(guia, idx, int(partes[4])))
            return

        if acao == "x":
            try:
                loja = LOJAS[int(partes[4])]
            except Exception:
                await q.edit_message_text("Loja inválida. Mande /link <url> de novo.")
                return
            if partes[5] == "0":
                await q.edit_message_text("✔️ Mantido o link antigo. Nada mudou.")
                return
            try:
                ok, lido = grava_link(prod, loja, url)
            except Exception as e:
                await q.edit_message_text("❌ Erro ao gravar: %s" % str(e)[:120])
                return
            await q.edit_message_text(
                ("🔁 Trocado!\n%s | %s\n%s" % (prod, loja, lido)) if ok
                else "⚠️ Troca sem confirmação de releitura.")
            return

    def link_handlers():
        """Handlers para o bot.py registrar (CommandHandler + CallbackQueryHandler)."""
        if not _TEM_PTB:
            return []
        return [CommandHandler("link", cmd_link),
                CallbackQueryHandler(on_lk, pattern=r"^lk:")]

    def link_conv_handler():
        """Mantido por compatibilidade: devolve o primeiro handler."""
        hs = link_handlers()
        return hs[0] if hs else None
else:
    def link_handlers():
        return []

    def link_conv_handler():
        return None
