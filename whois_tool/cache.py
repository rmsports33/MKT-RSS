"""whois_tool.cache — cache SQLite de respostas WHOIS com TTL."""
import sqlite3
import time
from pathlib import Path

DB = Path(__file__).parent.parent / ".cache" / "whois" / "cache.db"
TTL_PADRAO = 86400


class WhoisCache:
    def __init__(self, db_path=None, ttl: int = TTL_PADRAO):
        self.db_path = Path(db_path or DB)
        self.ttl = ttl
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.db_path)
        con.execute("CREATE TABLE IF NOT EXISTS whois (dominio TEXT PRIMARY KEY, resposta TEXT, ts REAL)")
        con.commit()
        con.close()

    def get(self, dominio: str):
        con = sqlite3.connect(self.db_path)
        cur = con.execute("SELECT resposta, ts FROM whois WHERE dominio=?", ((dominio or "").lower(),))
        row = cur.fetchone()
        con.close()
        if row and (time.time() - row[1] < self.ttl):
            return row[0]
        return None

    def set(self, dominio: str, resposta: str):
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT OR REPLACE INTO whois (dominio, resposta, ts) VALUES (?,?,?)",
                    ((dominio or "").lower(), resposta, time.time()))
        con.commit()
        con.close()
