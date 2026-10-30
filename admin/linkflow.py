"""Affiliate link helpers: URL/catalogue matching and Sheets operations.
The retired Telegram transport and handlers are no longer imported.
Writes remain explicit calls with existing validation and readback.
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
        raise ValueError("loja inválida: %s" % loja)
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
        raise ValueError("loja inválida: %s" % loja)
    rng = "'%s'!%s%d" % (ABA, COL[loja], mapa[produto])
    svc.spreadsheets().values().update(
        spreadsheetId=SID, range=rng, valueInputOption="RAW",
        body={"values": [[url]]}).execute()
    lido = le_celula(produto, loja, svc)
    return (lido == url, lido)



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
