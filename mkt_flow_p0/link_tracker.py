"""
mkt_flow_p0.link_tracker — Rastreabilidade P1.1
Cada link ganha ID único; registra onde foi publicado.
"""
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "mkt_flow_p0.db"

def init_link_tables():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS link_publicacoes (
        id TEXT PRIMARY KEY,
        link_id TEXT NOT NULL,
        link_original TEXT,
        plataforma TEXT,
        programa TEXT,
        url_publicacao TEXT,
        status_validacao TEXT,
        created_at TEXT
    )""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_link_pub_link_id ON link_publicacoes(link_id)")
    con.commit()
    con.close()

def gerar_link_id() -> str:
    return str(uuid.uuid4())[:8]

def registrar_publicacao(link_id: str, link_original: str, plataforma: str, programa: str, url_publicacao: str, status_validacao: str) -> str:
    init_link_tables()
    pub_id = str(uuid.uuid4())
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT INTO link_publicacoes (id, link_id, link_original, plataforma, programa, url_publicacao, status_validacao, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (pub_id, link_id, link_original, plataforma, programa, url_publicacao, status_validacao, datetime.now().isoformat()),
    )
    con.commit()
    con.close()
    return pub_id

def listar_publicacoes(link_id: str = None) -> list:
    init_link_tables()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    if link_id:
        cur = con.execute("SELECT * FROM link_publicacoes WHERE link_id=? ORDER BY created_at DESC", (link_id,))
    else:
        cur = con.execute("SELECT * FROM link_publicacoes ORDER BY created_at DESC LIMIT 100")
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows

def contar_por_plataforma() -> dict:
    init_link_tables()
    con = sqlite3.connect(DB_PATH)
    cur = con.execute("SELECT plataforma, COUNT(*) as c FROM link_publicacoes GROUP BY plataforma")
    d = {r[0]: r[1] for r in cur.fetchall()}
    con.close()
    return d
