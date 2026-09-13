import sqlite3, json
from datetime import datetime

DB_PATH = "mkt_flow.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-20000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS articles (id TEXT PRIMARY KEY, content TEXT, metadata TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, data TEXT, created_at TEXT, expires_at INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS credits (client_id TEXT, date TEXT, count INTEGER, PRIMARY KEY (client_id, date))''')
    c.execute('''CREATE TABLE IF NOT EXISTS cost_log (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, provider TEXT, tokens_input INTEGER, tokens_output INTEGER, cost REAL)''')
    # B1 (consolidação v3.11): orchestrator grava em affiliate_runs — criar aqui.
    # campaigns, link_publications (schema do link_tracker) e
    # platform_schedules (schema do scheduler) completam o núcleo.
    c.execute('''CREATE TABLE IF NOT EXISTS affiliate_runs (
        id TEXT PRIMARY KEY, link TEXT, status TEXT, plataforma TEXT,
        policy TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS campaigns (
        id TEXT PRIMARY KEY, nome TEXT, programa TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS link_publications (
        id TEXT PRIMARY KEY, campaign_id TEXT, link_original TEXT,
        plataforma TEXT, url_publicacao TEXT, status TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS platform_schedules (
        id TEXT PRIMARY KEY, campaign_id TEXT, content_id TEXT,
        plataforma TEXT, agendado_para TEXT, status TEXT, tentativas INTEGER DEFAULT 0,
        created_at TEXT)''')
    conn.commit()
    conn.close()