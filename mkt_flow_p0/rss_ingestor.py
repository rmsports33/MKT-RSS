"""
mkt_flow_p0.rss_ingestor — Ingestão RSS própria (P0)
Substitui cadastro de fonte de plugin terceiro (AINP/AI RSS Rewriter).
Pré-processamento externo: roda ANTES do LLM. Nunca inventa item.

Benchmark: usa feedparser (padrão mercado, grátis) + dedup por título
normalizado + similaridade >85% (mesma regra do YTI&W/AIWU).
"""
import hashlib
import logging
import re
import sqlite3
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List

import requests

try:
    import feedparser
    _HAS_FEEDPARSER = True
except ImportError:
    feedparser = None  # type: ignore
    _HAS_FEEDPARSER = False

logger = logging.getLogger("rss_ingestor")

DB_PATH = Path(__file__).parent.parent / "mkt_flow_p0.db"

# 4 fontes iniciais (Fase 1). Validadas em 12/09/2026 via teste local:
# - canaltech usa /rss/ (o /feed/ dá 404)
# - tecmundo devolve 204 vazio (anti-bot) → trocado por olhardigital
FEEDS_PADRAO: Dict[str, str] = {
    "tecnoblog": "https://tecnoblog.net/feed/",
    "canaltech": "https://canaltech.com.br/rss/",
    "olhardigital": "https://olhardigital.com.br/feed/",
    "adrenaline": "https://adrenaline.com.br/feed/",
}

_session = requests.Session()
_session.headers.update({"User-Agent": "Mozilla/5.0 (MKT-Flow-P0 RSS)"})

try:
    from .cloud_db import turso_enabled, turso_execute, turso_init_rss
except ImportError:  # uso standalone sem pacote
    from mkt_flow_p0.cloud_db import turso_enabled, turso_execute, turso_init_rss  # type: ignore


def _nuvem() -> bool:
    """True quando TURSO_* configurado (Actions/produção). Local segue SQLite."""
    try:
        return turso_enabled()
    except Exception:
        return False


def init_rss_tables():
    if _nuvem():
        r = turso_init_rss()
        if "erro" in r:
            logger.warning(f"rss turso init: {r['erro']}")
        return
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS rss_vistos (
        id TEXT PRIMARY KEY,
        fonte TEXT,
        url TEXT,
        titulo_norm TEXT,
        created_at TEXT
    )""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_rss_vistos_titulo ON rss_vistos(titulo_norm)")
    con.commit()
    con.close()


def _normalizar_titulo(t: str) -> str:
    t = (t or "").lower().strip()
    t = re.sub(r"\s+", " ", t)
    return t


def _id_url(url: str) -> str:
    return hashlib.sha256((url or "").encode()).hexdigest()[:16]


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def item_ja_visto(url: str, titulo: str) -> bool:
    """Dedup: mesma URL ou título >=85% similar já registrado (SQLite local ou Turso)."""
    init_rss_tables()
    norm = _normalizar_titulo(titulo)
    uid = _id_url(url)
    if _nuvem():
        r = turso_execute("SELECT 1 FROM rss_vistos WHERE id=?", (uid,))
        if r.get("rows"):
            return True
        r = turso_execute("SELECT titulo_norm FROM rss_vistos ORDER BY created_at DESC LIMIT 200")
        for linha in r.get("rows", []):
            existente = (linha or [None])[0]
            if existente and norm and _similar(norm, existente) >= 0.85:
                return True
        return False
    con = sqlite3.connect(DB_PATH)
    cur = con.execute("SELECT 1 FROM rss_vistos WHERE id=?", (uid,))
    if cur.fetchone():
        con.close()
        return True
    # Compara contra últimos 200 títulos (janela curta, barato)
    cur = con.execute("SELECT titulo_norm FROM rss_vistos ORDER BY created_at DESC LIMIT 200")
    for (existente,) in cur.fetchall():
        if existente and norm and _similar(norm, existente) >= 0.85:
            con.close()
            return True
    con.close()
    return False


def marcar_visto(fonte: str, url: str, titulo: str):
    init_rss_tables()
    if _nuvem():
        r = turso_execute(
            "INSERT OR IGNORE INTO rss_vistos (id, fonte, url, titulo_norm, created_at) VALUES (?,?,?,?,?)",
            (_id_url(url), fonte, url, _normalizar_titulo(titulo), datetime.now().isoformat()),
        )
        if "erro" in r:
            logger.warning(f"rss turso insert: {r['erro']}")
        return
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT OR IGNORE INTO rss_vistos (id, fonte, url, titulo_norm, created_at) VALUES (?,?,?,?,?)",
        (_id_url(url), fonte, url, _normalizar_titulo(titulo), datetime.now().isoformat()),
    )
    con.commit()
    con.close()


def fetch_feed(feed_url: str, fonte: str = "", timeout: int = 15, max_items: int = 10) -> dict:
    """
    Baixa 1 feed e devolve itens normalizados.
    Retorna {"fonte":..., "itens":[{titulo,link,published,resumo}], "total":N} ou {"erro":...}.
    """
    if not _HAS_FEEDPARSER:
        return {"erro": "feedparser não instalado — rode: pip install feedparser"}

    try:
        resp = _session.get(feed_url, timeout=timeout)
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
    except requests.Timeout:
        return {"erro": f"Feed timeout após {timeout}s: {feed_url}"}
    except Exception as e:
        return {"erro": f"Falha ao baixar feed: {str(e)[:150]}"}

    if getattr(parsed, "bozo", 0) and not getattr(parsed, "entries", None):
        return {"erro": f"Feed inválido ou vazio: {feed_url}"}

    itens: List[dict] = []
    for e in (parsed.entries or [])[:max_items]:
        titulo = (getattr(e, "title", "") or "").strip()
        link = (getattr(e, "link", "") or "").strip()
        if not titulo or not link:
            continue
        itens.append({
            "titulo": titulo,
            "link": link,
            "published": getattr(e, "published", "") or getattr(e, "updated", "") or "",
            "resumo": (getattr(e, "summary", "") or "")[:500],
            "fonte": fonte or feed_url,
        })
    return {"fonte": fonte or feed_url, "itens": itens, "total": len(itens)}


def buscar_novidades(feed_url: str, fonte: str = "", limit: int = 3, marcar: bool = True) -> dict:
    """
    Busca 1 feed, filtra já-vistos (dedup) e retorna só novidades.
    Se marcar=True, já registra como visto (evita reprocessar).
    """
    r = fetch_feed(feed_url, fonte=fonte, max_items=max(limit * 3, 10))
    if "erro" in r:
        return r
    novos = []
    for it in r["itens"]:
        if not item_ja_visto(it["link"], it["titulo"]):
            novos.append(it)
            if len(novos) >= limit:
                # marca só os que vai devolver (janela correta)
                break
    if marcar:
        for it in novos:
            marcar_visto(r["fonte"], it["link"], it["titulo"])
    return {"fonte": r["fonte"], "novos": novos, "total_novos": len(novos)}


def buscar_todos(limit_per_feed: int = 2) -> dict:
    """Roda os 4 feeds padrão. Retorna agregado por fonte."""
    resultado: Dict[str, dict] = {}
    total = 0
    for fonte, url in FEEDS_PADRAO.items():
        r = buscar_novidades(url, fonte=fonte, limit=limit_per_feed)
        resultado[fonte] = r
        if "novos" in r:
            total += len(r["novos"])
    return {"fontes": resultado, "total_novos": total}
