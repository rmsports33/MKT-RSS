"""MKTFLOW.link_tracker — rastreio clássico (v3.11 congelado). Campanhas + publicações + conflitos."""
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("mktflow.tracker")

DB = Path(__file__).parent / "mkt_flow.db"


def _con():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS campaigns (
        id TEXT PRIMARY KEY, nome TEXT, programa TEXT, created_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS link_publications (
        id TEXT PRIMARY KEY, campaign_id TEXT, link_original TEXT, plataforma TEXT,
        url_publicacao TEXT, status TEXT, created_at TEXT)""")
    return con


def create_campaign(nome: str, programa: str = "") -> dict:
    con = _con()
    cid = str(uuid.uuid4())[:8]
    con.execute("INSERT INTO campaigns (id, nome, programa, created_at) VALUES (?,?,?,?)",
                (cid, nome, programa, datetime.now().isoformat()))
    con.commit()
    con.close()
    return {"campaign_id": cid, "nome": nome, "programa": programa}


def register_publication(campaign_id: str, link_original: str, plataforma: str, url_publicacao: str, status: str = "PASS") -> dict:
    con = _con()
    pid = str(uuid.uuid4())
    con.execute("INSERT INTO link_publications (id, campaign_id, link_original, plataforma, url_publicacao, status, created_at)"
                " VALUES (?,?,?,?,?,?,?)",
                (pid, campaign_id, link_original, plataforma, url_publicacao, status, datetime.now().isoformat()))
    con.commit()
    con.close()
    return {"publication_id": pid, "campaign_id": campaign_id}


def get_link_history(link_original: str) -> list:
    con = _con()
    con.row_factory = sqlite3.Row
    cur = con.execute("SELECT * FROM link_publications WHERE link_original=? ORDER BY created_at DESC", (link_original,))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def list_links(campaign_id: str = "", limite: int = 100) -> list:
    con = _con()
    con.row_factory = sqlite3.Row
    if campaign_id:
        cur = con.execute("SELECT * FROM link_publications WHERE campaign_id=? ORDER BY created_at DESC LIMIT ?", (campaign_id, limite))
    else:
        cur = con.execute("SELECT * FROM link_publications ORDER BY created_at DESC LIMIT ?", (limite,))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def detect_link_conflicts(link_original: str = "") -> list:
    """Links publicados em 1 só plataforma de N ativas, ou duplicados na mesma plataforma."""
    pubs = list_links(limite=500)
    if link_original:
        pubs = [p for p in pubs if p.get("link_original") == link_original]
    vistos: dict = {}
    conflitos = []
    for p in pubs:
        chave = (p.get("link_original"), p.get("plataforma"))
        if chave in vistos:
            conflitos.append({"tipo": "duplicado", "link": p.get("link_original"), "plataforma": p.get("plataforma")})
        vistos[chave] = True
    return conflitos


def get_campaign_report(campaign_id: str) -> dict:
    pubs = list_links(campaign_id, limite=500)
    por_plat: dict = {}
    for p in pubs:
        por_plat[p.get("plataforma", "?")] = por_plat.get(p.get("plataforma", "?"), 0) + 1
    return {"campaign_id": campaign_id, "total": len(pubs), "por_plataforma": por_plat}
