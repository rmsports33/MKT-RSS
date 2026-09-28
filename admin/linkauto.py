# -*- coding: utf-8 -*-
"""admin/linkauto.py — /link v2: o bot DESCOBRE o produto sozinho pelo link.

Desenho (aprovado pelo dono em 28/09/2026):
  - 5 guias continuam como atalho rapido (codigo do linkflow, intocado).
  - /link <url> tenta LER a pagina (og:title/<title>) e sugere o produto.
  - Loja detectada pelo dominio (link.amazon -> Amazon).
  - Um botao "Buscar" le tipos+produtos DIRETO da planilha-mestre
    (nada de codigo novo quando a planilha crescer).
  - Um botao "Outro" (responder a mensagem com o nome) cobre o que a
    deteccao nao achou; se o modelo nao existir, o bot CRIA a linha com
    status "revisar" (controle de qualidade depois, sem travar o fluxo).

Destinos (regra):
  - produto dos 15 guias + loja das 5 -> aba "Links pendentes (5 guias)".
  - resto -> planilha-mestre (Página1): atualiza a linha (modelo, loja);
    se nao existir, cria [tipo, modelo, "", loja, url, "revisar"].

Stateless como o v1: estado no callback_data + no texto da mensagem.
"""
import html as _html
import logging
import os
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

import linkflow as LF  # noqa: E402  (norm_url, GUIAS, LOJAS, SID, _service, le_celula, grava_link)

logger = logging.getLogger("linkauto")

MESTRE = "Página1"
STATUS_REVISAR = "revisar"
GUIDE_SET = frozenset(p for _g, (_r, ps) in LF.GUIAS.items() for p in ps)
UA_NAV = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

LINK_HELP2 = ("/link <url> — registra link (descobre o produto sozinho)\n"
              "/link <url> | Nome do Produto — quando ele nao descobrir\n"
              "Na mensagem do bot: ✅ grava, 🔍 busca na planilha, ✍️ digita o nome")
USO2 = ("Uso: /link <url>\n"
        "Exemplo: /link https://www.amazon.com.br/dp/B0XXXXXXX\n"
        "Se ele nao descobrir o produto: /link <url> | Nome do Produto")

LOJA_ALIAS = (("a.co", "Amazon"), ("magalu", "Magazine Luiza"),
              ("mlivre", "Mercado Livre"))

TIPO_REGRAS = [
    ("Smartwatch", ["watch", "smartwatch", "relogio", "pulseira", "fit", "band"]),
    ("Smart TV", ["smart tv", "television", "polegada", "uhd", "qled", "oled", "qned",
                  "crystal", "tela", " 4k", " tv "]),
    ("Celular", ["celular", "smartphone", "iphone", "galaxy s", "moto g", "redmi", "poco",
                 "pixel", "galaxy a", "galaxy z"]),
    ("Notebook", ["notebook", "laptop", "vivobook", "ideapad", "macbook"]),
    ("Caixa de som", ["caixa de som", "caixa", "speaker", "soundbox", "soundbar", "blast",
                      "jbl", "echo"]),
    ("Teclado mecanico", ["teclado", "keyboard", "keychron"]),
]


# ---------------------------------------------------------------- texto puro
def _sem_acento(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()


def tokens(s):
    return re.findall(r"[a-z0-9]+", _sem_acento(s).lower())


def eh_modelo(tok):
    return bool(tok) and any(c.isdigit() for c in tok)


def limpa_titulo(t, maximo=90):
    t = _html.unescape(t or "")
    t = re.sub(r"\s+", " ", t).strip()
    return t[:maximo]


def extrai_titulo(url, getter=None, timeout=15):
    """Le a pagina e devolve {titulo, fonte, final, status}. Nunca explode."""
    import requests
    get = getter or requests.get
    try:
        r = get(url, headers=UA_NAV, timeout=timeout, allow_redirects=True)
    except Exception as e:  # noqa: BLE001
        return {"titulo": None, "fonte": None, "final": url, "status": "erro: %s" % str(e)[:50]}
    status = getattr(r, "status_code", None)
    final = getattr(r, "url", url) or url
    html = getattr(r, "text", "") or ""
    for padrao, fonte in (
            (r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', "og:title"),
            (r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']', "og:title"),
            (r"<title[^>]*>(.*?)</title>", "<title>"),
            (r'id=["\']productTitle["\'][^>]*>(.*?)</', "#productTitle")):
        m = re.search(padrao, html, re.I | re.S)
        if m:
            titulo = limpa_titulo(m.group(1), 200)
            if titulo:
                return {"titulo": titulo, "fonte": fonte, "final": final, "status": status}
    return {"titulo": None, "fonte": None, "final": final, "status": status}


def detecta_loja(url):
    """Dominio -> nome exato da loja (ou None)."""
    try:
        dom = re.sub(r"[^a-z]", "", urlparse(url or "").netloc.lower())
    except Exception:  # noqa: BLE001
        return None
    for loja in LF.LOJAS:
        nl = re.sub(r"[^a-z]", "", loja.lower())
        if nl and nl in dom:
            return loja
    for alias, loja in LOJA_ALIAS:
        if alias in dom:
            return loja
    return None


def guess_tipo(titulo):
    """Palpite de tipo pelo titulo (melhor esforco; fallback e perguntar)."""
    t = " " + _sem_acento(titulo or "").lower() + " "
    for tipo, chaves in TIPO_REGRAS:
        for k in chaves:
            if k in t:
                return tipo
    return None


def casa_modelo(consulta, modelos):
    """Casa texto livre contra a lista de modelos.
    forte: achou token de modelo (com digito) + pontos suficientes.
    fraco: pontos sem token de modelo (sugestao, com confirmacao).
    Devolve {"nivel": "forte"|"fraco"|"nada", "modelo": ..., "score": ...}."""
    qt = set(tokens(consulta))
    melhor, melhor_score, melhor_tm = None, -1, 0
    for modelo in modelos:
        mt = set(tokens(modelo))
        tm = {t for t in mt if eh_modelo(t)}
        hits_m = tm & qt
        hits_o = {t for t in mt - tm if len(t) >= 3} & qt
        score = 3 * len(hits_m) + len(hits_o)
        if score > melhor_score:
            melhor, melhor_score, melhor_tm = modelo, score, len(hits_m)
    if melhor_tm >= 1 and melhor_score >= 4:
        return {"nivel": "forte", "modelo": melhor, "score": melhor_score}
    if melhor_score >= 3:
        return {"nivel": "fraco", "modelo": melhor, "score": melhor_score}
    return {"nivel": "nada", "modelo": None, "score": melhor_score}


# ---------------------------------------------------------------- catalogo da mestre
_MESTRE_CACHE = None


def chave_modelo(modelo):
    return " ".join(tokens(modelo))


def catalogo_mestre(svc=None, force=False):
    """Le Página1!A:F uma vez por processo: {tipos: {tipo: [modelos]},
    linhas: {(modelo_norm, loja): {row, tipo, link}}}."""
    global _MESTRE_CACHE
    if _MESTRE_CACHE is not None and not force:
        return _MESTRE_CACHE
    svc = svc or LF._service()
    vals = svc.spreadsheets().values().get(
        spreadsheetId=LF.SID, range="'%s'!A:F" % MESTRE).execute().get("values", [])
    tipos, linhas = {}, {}
    for i, r in enumerate(vals[1:], start=2):
        r = (r + [""] * 6)[:6]
        tipo, modelo, loja, link = r[0].strip(), r[1].strip(), r[3].strip(), r[4].strip()
        if not modelo:
            continue
        if modelo not in tipos.setdefault(tipo, []):
            tipos[tipo].append(modelo)
        linhas[(chave_modelo(modelo), loja)] = {"row": i, "tipo": tipo, "link": link,
                                                "modelo": modelo}
    _MESTRE_CACHE = {"tipos": tipos, "linhas": linhas}
    return _MESTRE_CACHE


def limpa_cache_mestre():
    global _MESTRE_CACHE
    _MESTRE_CACHE = None


def grava_mestre(modelo, loja, url, svc=None):
    """Atualiza a linha (modelo, loja). Devolve (ok, detalhe)."""
    svc = svc or LF._service()
    cat = catalogo_mestre(svc)
    achada = cat["linhas"].get((chave_modelo(modelo), loja))
    if not achada:
        return (False, "sem-linha")
    rng = "'%s'!E%d" % (MESTRE, achada["row"])
    svc.spreadsheets().values().update(
        spreadsheetId=LF.SID, range=rng, valueInputOption="RAW",
        body={"values": [[url]]}).execute()
    volta = svc.spreadsheets().values().get(
        spreadsheetId=LF.SID, range=rng).execute().get("values", [])
    lido = (volta[0][0] if volta and volta[0] else "").strip()
    return (lido == url, lido or "divergiu-na-releitura")


def cria_linha_mestre(tipo, modelo, loja, url, svc=None):
    """Acrescenta [tipo, modelo, '', loja, url, 'revisar']. Devolve True/False."""
    svc = svc or LF._service()
    try:
        svc.spreadsheets().values().append(
            spreadsheetId=LF.SID, range="'%s'!A:F" % MESTRE, valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [[tipo, modelo, "", loja, url, STATUS_REVISAR]]}).execute()
        limpa_cache_mestre()
        return True
    except Exception as e:  # noqa: BLE001
        logger.warning("cria_linha_mestre falhou: %s", e)
        return False


def grava_destino(produto, loja, url, tipo=None, svc=None):
    """Roteador: guia (15) -> aba dos guias; resto -> mestre (cria se faltar tipo).
    Devolve (destino, ok, detalhe)."""
    if produto in GUIDE_SET and loja in LF.LOJAS:
        ok, lido = LF.grava_link(produto, loja, url)
        return ("guia", ok, lido)
    ok, det = grava_mestre(produto, loja, url, svc)
    if ok:
        return ("mestre", True, det)
    if det != "sem-linha" or not tipo:
        return ("mestre", False, det if det != "sem-linha" else "falta-tipo")
    if cria_linha_mestre(tipo, produto, loja, url, svc):
        return ("mestre-nova", True, "linha criada (status revisar)")
    return ("mestre", False, "falha-ao-criar")


# ---------------------------------------------------------------- mensagens (parse reverso)
def parse_linhas(texto):
    """Le de volta 🔗/📦/🏷️/🏪 do texto da mensagem. Puro e testavel."""
    out = {}
    for ln in (texto or "").splitlines():
        ln = ln.strip()
        for emoji, chave in (("🔗", "url"), ("📦", "modelo"), ("🏷️", "tipo"), ("🏪", "loja")):
            if ln.startswith(emoji):
                out[chave] = ln[len(emoji):].strip()
    return out


def msg_confirm(url, modelo, loja):
    return ("🔗 %s\n📦 %s\n🏪 %s\n\nConfirma e grava?" % (url, modelo, loja or "—"))


# ---------------------------------------------------------------- Telegram (opcional)
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import (CommandHandler, CallbackQueryHandler, ContextTypes,
                              MessageHandler, filters)
    _TEM_PTB = True
except ImportError:
    _TEM_PTB = False

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

    def _kb_confirm():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Gravar", callback_data="lk:ok:")],
            [InlineKeyboardButton("🔍 Buscar na planilha", callback_data="lk:b:"),
             InlineKeyboardButton("✍️ Outro nome", callback_data="lk:o:")],
            [InlineKeyboardButton("🏪 Trocar a loja", callback_data="lk:sl:")],
        ])

    def _kb_guias2():
        fileiras = [[InlineKeyboardButton("⌚ Smartwatch", callback_data="lk:g:smartwatch")],
                    [InlineKeyboardButton("📺 TV 4K", callback_data="lk:g:tv4k")],
                    [InlineKeyboardButton("💻 Notebook", callback_data="lk:g:notebook")],
                    [InlineKeyboardButton("🔊 Caixa de som", callback_data="lk:g:caixa_som")],
                    [InlineKeyboardButton("⌨️ Teclado", callback_data="lk:g:teclado")],
                    [InlineKeyboardButton("🔍 Buscar na planilha", callback_data="lk:b:"),
                     InlineKeyboardButton("✍️ Outro nome", callback_data="lk:o:")]]
        return InlineKeyboardMarkup(fileiras)

    def _kb_tipos(tipos):
        fileiras = [[InlineKeyboardButton(t, callback_data="lk:bt:%d" % i)]
                    for i, t in enumerate(tipos)]
        return InlineKeyboardMarkup(fileiras)

    def _kb_prods_mestre(ti, prods):
        fileiras = [[InlineKeyboardButton(p, callback_data="lk:bp:%d:%d" % (ti, i))]
                    for i, p in enumerate(prods)]
        fileiras.append([InlineKeyboardButton("➕ Cadastrar novo", callback_data="lk:bn:%d" % ti)])
        fileiras.append([InlineKeyboardButton("⬅️ Tipos", callback_data="lk:b:")])
        return InlineKeyboardMarkup(fileiras)

    def _kb_lojas2(ti, pi):
        base = "lk:bl:%d:%d:" % (ti, pi)
        fileiras = [[InlineKeyboardButton("%d. %s" % (i + 1, l), callback_data=base + str(i))]
                    for i, l in enumerate(LF.LOJAS)]
        fileiras.append([InlineKeyboardButton("⬅️ Produtos", callback_data="lk:bt:%d" % ti)])
        return InlineKeyboardMarkup(fileiras)

    def _tipos_ordenados(svc=None):
        return sorted(catalogo_mestre(svc)["tipos"].keys())

    async def cmd_link2(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/link v2: tenta descobrir o produto sozinho."""
        if not _permitido(update):
            await _negado(update)
            return
        bruto = " ".join(context.args or [])
        parte_url, _, nome_dado = bruto.partition("|")
        url = LF.norm_url(parte_url)
        if not url:
            await update.message.reply_text(LF.USO2 if hasattr(LF, "USO2") else
                                            ("Uso: /link <url>\nExemplo: /link "
                                             "https://www.amazon.com.br/dp/B0XXXXXXX"))
            return
        try:
            det = extrai_titulo(url)
        except Exception as e:  # noqa: BLE001
            det = {"titulo": None, "fonte": None, "final": url, "status": "erro: %s" % str(e)[:40]}
        loja = detecta_loja(det.get("final") or url) or detecta_loja(url)
        logger.info("/link v2 de uid=%s: %s (titulo=%s, loja=%s)",
                    getattr(getattr(update, "effective_user", None), "id", "?"),
                    url[:80], (det.get("titulo") or "")[:60], loja)
        modelos = list(GUIDE_SET) + [m for ts in catalogo_mestre()["tipos"].values() for m in ts]
        consulta = (nome_dado.strip() + " " + (det.get("titulo") or "")).strip()
        m = casa_modelo(consulta, modelos) if consulta else {"nivel": "nada"}
        if m["nivel"] == "forte":
            await update.message.reply_text(
                "🔗 %s\n📦 %s\n🏪 %s%s\n\nConfirma e grava?"
                % (url, m["modelo"], loja or "não detectada",
                   "" if loja else " — escolha abaixo"),
                reply_markup=_kb_confirm() if loja else _kb_lojas_livres())
            return
        if m["nivel"] == "fraco":
            # formato parseavel de proposito: o ✅ (lk:ok:) le 📦/🏪/🔗 do texto
            await update.message.reply_text(
                "🔗 %s\n📦 %s\n🏪 %s\n\nNão tenho certeza. É esse?"
                % (url, m["modelo"], loja or "—"),
                reply_markup=_kb_confirm() if loja else _kb_lojas_livres())
            return
        await update.message.reply_text(
            "🔗 %s\n%s\n\nNão reconheci o produto. Escolha o caminho:" % (
                url, ("🏪 %s" % loja + "\n" if loja else "")),
            reply_markup=_kb_guias2())

    def _modelo_confirmado(texto, loja_idx=None):
        """Reconstroi (url, modelo, loja) do texto da mensagem de confirmacao."""
        d = parse_linhas(texto)
        url, modelo = d.get("url"), d.get("modelo")
        loja = d.get("loja")
        if loja_idx is not None:
            loja = LF.LOJAS[loja_idx]
        if loja == "—" or loja == "não detectada":
            loja = None
        return url, modelo, loja

    async def on_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        try:
            await q.answer()
        except Exception:
            pass
        if not _permitido(update):
            await _negado(update)
            return
        partes = (q.data or "").split(":")
        if not partes or partes[0] != "lk":
            return
        msg = getattr(q, "message", None)
        texto = getattr(msg, "text", "") or ""
        acao = partes[1] if len(partes) > 1 else ""

        if acao == "b":
            try:
                tipos = _tipos_ordenados()
            except Exception as e:  # noqa: BLE001
                await q.edit_message_text("❌ Erro ao ler a planilha: %s" % str(e)[:120])
                return
            url = parse_linhas(texto).get("url", "")
            await q.edit_message_text("🔗 %s\n\nQual tipo?" % url, reply_markup=_kb_tipos(tipos))
            return

        if acao == "bt":
            try:
                tipos = _tipos_ordenados()
                tipo = tipos[int(partes[2])]
                prods = catalogo_mestre()["tipos"][tipo]
            except Exception:
                await q.edit_message_text("Tipo inválido. Toque em 🔍 de novo.")
                return
            url = parse_linhas(texto).get("url", "")
            await q.edit_message_text("🔗 %s\n🔍 %s\n\nQual produto?" % (url, tipo),
                                      reply_markup=_kb_prods_mestre(
                                          tipos.index(tipo), prods))
            return

        if acao == "bp":
            try:
                tipos = _tipos_ordenados()
                tipo = tipos[int(partes[2])]
                modelo = catalogo_mestre()["tipos"][tipo][int(partes[3])]
            except Exception:
                await q.edit_message_text("Produto inválido. Toque em 🔍 de novo.")
                return
            url = parse_linhas(texto).get("url", "")
            loja = detecta_loja(url)
            await q.edit_message_text(
                "🔗 %s\n📦 %s%s\n\nQual loja?" % (
                    url, modelo, "\n🏪 %s (detectada)" % loja if loja else ""),
                reply_markup=_kb_lojas2(tipos.index(tipo),
                                        catalogo_mestre()["tipos"][tipo].index(modelo)))
            return

        if acao == "bn":
            url = parse_linhas(texto).get("url", "")
            loja = detecta_loja(url)
            await q.edit_message_text(
                "🔗 %s%s\n\n✍️ Responda ESTA mensagem com o nome do produto "
                "(ex.: Galaxy S25 FE)." % (url, "\n🏪 %s" % loja if loja else ""))
            return

        if acao == "o":
            url = parse_linhas(texto).get("url", "")
            await q.edit_message_text(
                "🔗 %s\n\n✍️ Responda ESTA mensagem com o nome do produto." % url)
            return

        if acao == "bl":
            try:
                tipos = _tipos_ordenados()
                tipo = tipos[int(partes[2])]
                modelo = catalogo_mestre()["tipos"][tipo][int(partes[3])]
                loja = LF.LOJAS[int(partes[4])]
            except Exception:
                await q.edit_message_text("Escolha inválida. Toque em 🔍 de novo.")
                return
            url = parse_linhas(texto).get("url", "")
            try:
                dest, ok, det = grava_destino(modelo, loja, url, tipo)
            except Exception as e:  # noqa: BLE001
                await q.edit_message_text("❌ Erro ao gravar: %s" % str(e)[:120])
                return
            await q.edit_message_text(_texto_resultado(dest, ok, det, modelo, loja))
            return

        if acao == "t":
            d = parse_linhas(texto)
            url, modelo, loja = d.get("url"), d.get("modelo"), d.get("loja")
            try:
                tipo = _tipos_ordenados()[int(partes[2])]
            except Exception:
                await q.edit_message_text("Tipo inválido. Comece de novo com /link.")
                return
            if not (url and modelo and loja):
                await q.edit_message_text("Faltou dado. Comece de novo com /link.")
                return
            try:
                dest, ok, det = grava_destino(modelo, loja, url, tipo)
            except Exception as e:  # noqa: BLE001
                await q.edit_message_text("❌ Erro ao gravar: %s" % str(e)[:120])
                return
            await q.edit_message_text(_texto_resultado(dest, ok, det, modelo, loja))
            return

        if acao == "tl":
            # loja escolhida no fluxo de criar (dominio desconhecido): volta
            # para a pergunta do tipo, agora com a loja preenchida.
            d = parse_linhas(texto)
            url, modelo = d.get("url"), d.get("modelo")
            try:
                loja = LF.LOJAS[int(partes[2])]
                tipos = _tipos_ordenados()
            except Exception:
                await q.edit_message_text("Escolha inválida. Comece de novo com /link.")
                return
            if not (url and modelo):
                await q.edit_message_text("Faltou dado. Comece de novo com /link.")
                return
            await q.edit_message_text(
                "🔗 %s\n📦 %s\n🏪 %s\n\nNão encontrei. Criar novo? Escolha o tipo:"
                % (url, modelo, loja), reply_markup=_kb_tipos(tipos))
            return

        if acao == "ok":
            url, modelo, loja = _modelo_confirmado(texto)
            if not (url and modelo and loja):
                await q.edit_message_text(
                    "Faltou a loja. Toque em 🏪 Trocar a loja e escolha.")
                return
            try:
                dest, ok, det = grava_destino(modelo, loja, url)
            except Exception as e:  # noqa: BLE001
                await q.edit_message_text("❌ Erro ao gravar: %s" % str(e)[:120])
                return
            await q.edit_message_text(_texto_resultado(dest, ok, det, modelo, loja))
            return

        if acao == "sl":
            d = parse_linhas(texto)
            url, modelo = d.get("url"), d.get("modelo")
            try:
                loja = LF.LOJAS[int(partes[2])]
            except Exception:
                await q.edit_message_text("Loja inválida.")
                return
            if not (url and modelo):
                await q.edit_message_text("Faltou dado. Comece de novo com /link.")
                return
            await q.edit_message_text(msg_confirm(url, modelo, loja),
                                      reply_markup=_kb_confirm())
            return

    def _texto_resultado(dest, ok, det, modelo, loja):
        if ok and dest == "guia":
            return "✅ Gravado na aba dos guias!\n%s | %s\n%s" % (modelo, loja, det)
        if ok and dest == "mestre":
            return "✅ Gravado na planilha mestre!\n%s | %s" % (modelo, loja)
        if ok and dest == "mestre-nova":
            return ("✅ Criado na planilha mestre e gravado!\n%s | %s\n"
                    "⚠️ Marquei como *revisar* — confira o tipo depois." % (modelo, loja))
        return "❌ Não gravou (%s). Tente de novo." % det

    async def on_resposta(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Resposta a uma mensagem do bot (o ✍️ Outro). Stateless via reply."""
        msg = getattr(update, "message", None)
        if msg is None:
            return
        if not _permitido(update):
            await _negado(update)
            return
        origem = getattr(msg, "reply_to_message", None)
        if origem is None:
            return
        url = parse_linhas(getattr(origem, "text", "") or "").get("url")
        if not url:
            return
        nome = (getattr(msg, "text", "") or "").strip()[:80]
        if not nome:
            return
        loja = detecta_loja(url)
        modelos = list(GUIDE_SET) + [m for ts in catalogo_mestre()["tipos"].values()
                                     for m in ts]
        m = casa_modelo(nome, modelos)
        if m["nivel"] == "forte":
            await msg.reply_text(
                msg_confirm(url, m["modelo"], loja or "—"),
                reply_markup=_kb_confirm() if loja else _kb_lojas_livres())
            return
        if m["nivel"] == "fraco":
            await msg.reply_text(
                "🔗 %s\n📦 %s\n🏪 %s\n\nNão tenho certeza. É esse?"
                % (url, m["modelo"], loja or "—"),
                reply_markup=_kb_confirm() if loja else _kb_lojas_livres())
            return
        try:
            tipos = _tipos_ordenados()
        except Exception as e:  # noqa: BLE001
            await msg.reply_text("❌ Erro ao ler a planilha: %s" % str(e)[:120])
            return
        if not loja:
            await msg.reply_text(
                "🔗 %s\n📦 %s\n\nNão encontrei — e não detectei a loja. Qual loja?"
                % (url, nome), reply_markup=_kb_lojas_tl())
            return
        await msg.reply_text(
            "🔗 %s\n📦 %s%s\n\nNão encontrei. Criar novo? Escolha o tipo:"
            % (url, nome, "\n🏪 %s" % loja if loja else ""),
            reply_markup=_kb_tipos(tipos))

    def _kb_lojas_livres():
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("%d. %s" % (i + 1, l), callback_data="lk:sl:%d" % i)]
             for i, l in enumerate(LF.LOJAS)])

    def _kb_lojas_tl():
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("%d. %s" % (i + 1, l), callback_data="lk:tl:%d" % i)]
             for i, l in enumerate(LF.LOJAS)])

    def linkauto_handlers():
        if not _TEM_PTB:
            return []
        return [CommandHandler("link", cmd_link2),
                CallbackQueryHandler(on_auto, pattern=r"^lk:(bt|bp|bl|bn|tl|sl|ok|b|o|t)(:|$|:.+)"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, on_resposta)]
else:
    def linkauto_handlers():
        return []
