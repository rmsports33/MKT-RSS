# -*- coding: utf-8 -*-
"""Affiliate link helpers: URL/catalogue matching and Sheets operations.
The retired Telegram transport and handlers are no longer imported.
Writes remain explicit calls with existing validation and readback.
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
