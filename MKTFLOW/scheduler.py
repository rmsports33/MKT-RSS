"""MKTFLOW.scheduler — agendador clássico (v3.11 congelado). SQLite em MKTFLOW/mkt_flow.db."""
import logging
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("mktflow.scheduler")

DB = Path(__file__).parent / "mkt_flow.db"
BACKOFF = [5, 15, 60]
MAX_TENT = 3


def _con():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS platform_schedules (
        id TEXT PRIMARY KEY, campaign_id TEXT, content_id TEXT, plataforma TEXT,
        agendado_para TEXT, status TEXT DEFAULT 'agendado', tentativas INTEGER DEFAULT 0,
        created_at TEXT)""")
    return con


def get_platform_limits(plataforma: str) -> dict:
    base = {
        "instagram": {"max_posts_per_day": 5},
        "tiktok": {"max_posts_per_day": 10},
        "pinterest": {"max_posts_per_day": 20},
        "wordpress": {"max_posts_per_day": 50},
    }
    return dict(base.get((plataforma or "").lower(), {"max_posts_per_day": 5}))


def schedule_post(content_id: str, plataforma: str, agendado_para: str = "", campaign_id: str = "") -> dict:
    con = _con()
    sid = str(uuid.uuid4())[:8]
    quando = agendado_para or datetime.now().isoformat()
    con.execute("INSERT INTO platform_schedules (id, campaign_id, content_id, plataforma, agendado_para, status, tentativas, created_at)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (sid, campaign_id, content_id, plataforma, quando, "agendado", 0, datetime.now().isoformat()))
    con.commit()
    con.close()
    return {"schedule_id": sid, "status": "agendado", "agendado_para": quando}


def schedule_campaign(content_id: str, plataformas: list, campaign_id: str = "", espacamento_horas: int = 2) -> dict:
    base = datetime.now()
    ids = [schedule_post(content_id, p, (base + timedelta(hours=i * espacamento_horas)).isoformat(), campaign_id)["schedule_id"]
           for i, p in enumerate(plataformas or [])]
    return {"campaign_id": campaign_id or str(uuid.uuid4())[:8], "schedules": ids, "total": len(ids)}


def get_due_posts(agora: str = "") -> list:
    con = _con()
    con.row_factory = sqlite3.Row
    cur = con.execute("SELECT * FROM platform_schedules WHERE status='agendado' AND agendado_para<=? AND tentativas<? ORDER BY agendado_para",
                      (agora or datetime.now().isoformat(), MAX_TENT))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def mark_published(schedule_id: str) -> bool:
    con = _con()
    cur = con.execute("UPDATE platform_schedules SET status='publicado' WHERE id=?", (schedule_id,))
    ok = cur.rowcount > 0
    con.commit()
    con.close()
    return ok


def mark_failed(schedule_id: str) -> dict:
    con = _con()
    cur = con.execute("SELECT tentativas FROM platform_schedules WHERE id=?", (schedule_id,))
    row = cur.fetchone()
    if not row:
        con.close()
        return {"ok": False, "erro": "schedule inexistente"}
    tent = (row[0] or 0) + 1
    if tent >= MAX_TENT:
        con.execute("UPDATE platform_schedules SET status='falhou', tentativas=? WHERE id=?", (tent, schedule_id))
        con.commit()
        con.close()
        return {"ok": True, "status": "falhou"}
    novo = (datetime.now() + timedelta(minutes=BACKOFF[min(tent - 1, len(BACKOFF) - 1)])).isoformat()
    con.execute("UPDATE platform_schedules SET tentativas=?, agendado_para=? WHERE id=?", (tent, novo, schedule_id))
    con.commit()
    con.close()
    return {"ok": True, "status": "agendado", "tentativas": tent}


def list_schedules(status: str = "", limite: int = 100) -> list:
    con = _con()
    con.row_factory = sqlite3.Row
    if status:
        cur = con.execute("SELECT * FROM platform_schedules WHERE status=? ORDER BY agendado_para DESC LIMIT ?", (status, limite))
    else:
        cur = con.execute("SELECT * FROM platform_schedules ORDER BY agendado_para DESC LIMIT ?", (limite,))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def get_calendar_view(inicio: str, fim: str) -> dict:
    dias: dict = {}
    for s in list_schedules(limite=500):
        ap = s.get("agendado_para") or ""
        if inicio <= ap <= fim:
            dias.setdefault(ap[:10], []).append(s)
    return {"dias": dias, "total": sum(len(v) for v in dias.values())}


def clear_schedules() -> int:
    con = _con()
    cur = con.execute("DELETE FROM platform_schedules")
    n = cur.rowcount
    con.commit()
    con.close()
    return n
