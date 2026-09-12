"""
mkt_flow_p0.scheduler — Agendamento multi-plataforma (P1.3).
SQLite local (tabela platform_schedules). Retry com backoff.
Respeita limites do vault (get_platform_limits) quando disponível.
"""
import logging
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("scheduler")

DB_PATH = Path(__file__).parent.parent / "mkt_flow_p0.db"
BACKOFF_MINUTES = [5, 15, 60]
MAX_TENTATIVAS = 3


def init_scheduler_tables():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS platform_schedules (
        id TEXT PRIMARY KEY,
        campaign_id TEXT,
        content_id TEXT,
        link_id TEXT,
        plataforma TEXT,
        identidade_id TEXT,
        agendado_para TEXT,
        status TEXT DEFAULT 'agendado',
        tentativas INTEGER DEFAULT 0,
        created_at TEXT
    )""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_sched_status ON platform_schedules(status, agendado_para)")
    con.commit()
    con.close()


def get_platform_limits(plataforma: str) -> dict:
    """Limites por plataforma; delega ao vault quando disponível (P3 compat)."""
    try:
        from mkt_flow_p0.vault import get_platform_limits as vault_limits
        lim = vault_limits(plataforma)
        if lim:
            return lim
    except Exception:
        pass
    padrao = {
        "instagram": {"max_posts_per_day": 5, "observacao": "sem link clicável no corpo — usar link na bio"},
        "tiktok": {"max_posts_per_day": 10, "observacao": "sem link clicável — bio/comentário"},
        "pinterest": {"max_posts_per_day": 20, "observacao": "link permitido no pin"},
        "wordpress": {"max_posts_per_day": 50, "observacao": "link permitido no corpo"},
    }
    return padrao.get((plataforma or "").lower(), {"max_posts_per_day": 5, "observacao": "limite padrão"})


def schedule_post(content_id: str, plataforma: str, agendado_para: str = "",
                  campaign_id: str = "", link_id: str = "", identidade_id: str = "") -> dict:
    """Agenda 1 post. agendado_para ISO; vazio = agora."""
    init_scheduler_tables()
    sid = str(uuid.uuid4())[:8]
    quando = agendado_para or datetime.now().isoformat()
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT INTO platform_schedules (id, campaign_id, content_id, link_id, plataforma, identidade_id, agendado_para, status, tentativas, created_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?)",
        (sid, campaign_id, content_id, link_id, plataforma, identidade_id, quando, "agendado", 0, datetime.now().isoformat()),
    )
    con.commit()
    con.close()
    return {"schedule_id": sid, "status": "agendado", "agendado_para": quando}


def schedule_campaign(content_id: str, plataformas: list, campaign_id: str = "", link_id: str = "",
                      espacamento_horas: int = 2) -> dict:
    """Agenda 1 conteúdo em N plataformas com espaçamento (estratégia optimal simples)."""
    base = datetime.now()
    ids = []
    for i, plat in enumerate(plataformas or []):
        quando = (base + timedelta(hours=i * espacamento_horas)).isoformat()
        r = schedule_post(content_id, plat, quando, campaign_id, link_id)
        ids.append(r["schedule_id"])
    return {"campaign_id": campaign_id or str(uuid.uuid4())[:8], "schedules": ids, "total": len(ids)}


def get_due_posts(agora: str = "") -> list:
    """Posts agendados com hora <= agora e tentativas < max."""
    init_scheduler_tables()
    agora = agora or datetime.now().isoformat()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.execute(
        "SELECT * FROM platform_schedules WHERE status='agendado' AND agendado_para<=? AND tentativas<? ORDER BY agendado_para",
        (agora, MAX_TENTATIVAS),
    )
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def mark_published(schedule_id: str) -> bool:
    return _set_status(schedule_id, "publicado")


def mark_failed(schedule_id: str) -> dict:
    """Falha com backoff: reagenda (tentativas+1) ou desiste após MAX_TENTATIVAS."""
    init_scheduler_tables()
    con = sqlite3.connect(DB_PATH)
    cur = con.execute("SELECT tentativas FROM platform_schedules WHERE id=?", (schedule_id,))
    row = cur.fetchone()
    if not row:
        con.close()
        return {"ok": False, "erro": "schedule inexistente"}
    tent = (row[0] or 0) + 1
    if tent >= MAX_TENTATIVAS:
        con.execute("UPDATE platform_schedules SET status='falhou', tentativas=? WHERE id=?", (tent, schedule_id))
        con.commit()
        con.close()
        return {"ok": True, "status": "falhou"}
    espera = BACKOFF_MINUTES[min(tent - 1, len(BACKOFF_MINUTES) - 1)]
    novo = (datetime.now() + timedelta(minutes=espera)).isoformat()
    con.execute("UPDATE platform_schedules SET tentativas=?, agendado_para=? WHERE id=?", (tent, novo, schedule_id))
    con.commit()
    con.close()
    return {"ok": True, "status": "agendado", "tentativas": tent, "reagendado_para": novo}


def _set_status(schedule_id: str, status: str) -> bool:
    init_scheduler_tables()
    con = sqlite3.connect(DB_PATH)
    cur = con.execute("UPDATE platform_schedules SET status=? WHERE id=?", (status, schedule_id))
    ok = cur.rowcount > 0
    con.commit()
    con.close()
    return ok


def list_schedules(status: str = "", limite: int = 100) -> list:
    init_scheduler_tables()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    if status:
        cur = con.execute("SELECT * FROM platform_schedules WHERE status=? ORDER BY agendado_para DESC LIMIT ?", (status, limite))
    else:
        cur = con.execute("SELECT * FROM platform_schedules ORDER BY agendado_para DESC LIMIT ?", (limite,))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def get_calendar_view(inicio: str, fim: str) -> dict:
    """Visão calendário: {data: [posts]} + avisos de capacidade."""
    init_scheduler_tables()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.execute(
        "SELECT * FROM platform_schedules WHERE agendado_para>=? AND agendado_para<=? ORDER BY agendado_para",
        (inicio, fim),
    )
    dias: dict = {}
    for r in cur.fetchall():
        d = dict(r)
        dia = (d.get("agendado_para") or "")[:10]
        dias.setdefault(dia, []).append(d)
    con.close()
    avisos = []
    for dia, posts in dias.items():
        por_plat: dict = {}
        for p in posts:
            por_plat[p.get("plataforma")] = por_plat.get(p.get("plataforma"), 0) + 1
        for plat, qtd in por_plat.items():
            lim = get_platform_limits(plat).get("max_posts_per_day", 5)
            if qtd > lim:
                avisos.append(f"{dia}: {plat} com {qtd} posts (limite {lim}/dia)")
    return {"dias": dias, "avisos_capacidade": avisos}


def clear_schedules() -> int:
    """Limpa tudo (uso em testes). Retorna removidos."""
    init_scheduler_tables()
    con = sqlite3.connect(DB_PATH)
    cur = con.execute("DELETE FROM platform_schedules")
    n = cur.rowcount
    con.commit()
    con.close()
    return n
