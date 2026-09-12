"""
mkt_flow_p0.vault — Vault de identidades por plataforma (P3).
Guarda contas (Instagram, TikTok...) + limites; tokens nunca vão para log.
SQLite local. Usado pelo scheduler para respeitar rate limits (P3 compat).
"""
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("vault")

DB_PATH = Path(__file__).parent.parent / "mkt_flow_p0.db"

PLATFORM_LIMITS = {
    "instagram": {"max_posts_per_day": 5, "max_video_seconds": 3600, "link_no_corpo": False},
    "tiktok": {"max_posts_per_day": 10, "max_video_seconds": 600, "link_no_corpo": False},
    "pinterest": {"max_posts_per_day": 20, "max_video_seconds": 900, "link_no_corpo": True},
    "linkedin": {"max_posts_per_day": 1, "max_video_seconds": 600, "link_no_corpo": True},
    "wordpress": {"max_posts_per_day": 50, "max_video_seconds": 0, "link_no_corpo": True},
}

# Compat programa x plataforma (para agendar_com_programa): False = combinação bloqueada
COMPAT_PROGRAMA_PLATAFORMA = {
    ("mercado_livre", "instagram"): True,
    ("mercado_livre", "tiktok"): True,
    ("mercado_livre", "pinterest"): True,
    ("mercado_livre", "wordpress"): True,
    ("shopee", "instagram"): True,
    ("shopee", "tiktok"): True,
    ("shopee", "pinterest"): True,
    ("shopee", "wordpress"): False,  # SH-AFFILIATE-URL-INDEX: sem indexação orgânica de URL com ID
}


def init_vault_tables():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS platform_identities (
        id TEXT PRIMARY KEY,
        plataforma TEXT NOT NULL,
        conta TEXT NOT NULL,
        afiliado_id TEXT DEFAULT '',
        token_ref TEXT DEFAULT '',
        nicho TEXT DEFAULT '',
        created_at TEXT
    )""")
    con.commit()
    con.close()


def get_platform_limits(plataforma: str) -> dict:
    return dict(PLATFORM_LIMITS.get((plataforma or "").lower(), {"max_posts_per_day": 5, "link_no_corpo": False}))


def registrar_identidade(plataforma: str, conta: str, afiliado_id: str = "", token_ref: str = "", nicho: str = "") -> dict:
    """Registra conta. Guarda só referência do token, nunca o segredo."""
    init_vault_tables()
    iid = f"identity_{(plataforma or 'x').lower()}_{str(uuid.uuid4())[:6]}"
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT INTO platform_identities (id, plataforma, conta, afiliado_id, token_ref, nicho, created_at)"
        " VALUES (?,?,?,?,?,?,?)",
        (iid, plataforma, conta, afiliado_id, token_ref, nicho, datetime.now().isoformat()),
    )
    con.commit()
    con.close()
    return {"identity_id": iid, "plataforma": plataforma, "conta": conta}


def listar_identidades(plataforma: str = "") -> list:
    init_vault_tables()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    if plataforma:
        cur = con.execute("SELECT id, plataforma, conta, afiliado_id, nicho, created_at FROM platform_identities WHERE plataforma=?", (plataforma,))
    else:
        cur = con.execute("SELECT id, plataforma, conta, afiliado_id, nicho, created_at FROM platform_identities")
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def checar_compatibilidade(programa: str, plataforma: str) -> dict:
    """Diz se programa pode publicar na plataforma (ex.: Shopee x WP orgânico)."""
    ok = COMPAT_PROGRAMA_PLATAFORMA.get(((programa or "").lower(), (plataforma or "").lower()), True)
    motivo = "" if ok else "Combinação bloqueada por policy (ex.: SH-AFFILIATE-URL-INDEX p/ indexação orgânica)"
    return {"compativel": ok, "motivo": motivo}


def agendar_com_programa(programa: str, plataforma: str, content_id: str, **kwargs) -> dict:
    """Atalho com gate: valida compat antes de agendar no scheduler."""
    gate = checar_compatibilidade(programa, plataforma)
    if not gate["compativel"]:
        return {"erro": gate["motivo"], "compativel": False}
    from mkt_flow_p0.scheduler import schedule_post
    r = schedule_post(content_id, plataforma, **kwargs)
    r["compativel"] = True
    return r
