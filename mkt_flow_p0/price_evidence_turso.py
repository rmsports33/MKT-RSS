"""Shopee SQLite -> Turso homolog: allowlisted, fail-closed and idempotent.

The local SQLite source is opened read-only. Never writes to WordPress,
production Turso, or the local evidence file.
Python >=3.6 compatible.
"""
import hashlib
import re
import sqlite3
from pathlib import Path
from urllib.parse import urlsplit

HOMOLOG_HOST = "mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io"
TABLE = "conexo_price_evidence_v1"
SQL_CREATE = (
    "CREATE TABLE IF NOT EXISTS " + TABLE + " ("
    "evidence_id TEXT PRIMARY KEY, produto TEXT NOT NULL, marketplace TEXT NOT NULL, "
    "preco_br TEXT NOT NULL, data_captura TEXT NOT NULL, url_oferta TEXT NOT NULL, "
    "hash_local TEXT NOT NULL)"
)
SQL_INSERT = (
    "INSERT OR IGNORE INTO " + TABLE +
    " (evidence_id,produto,marketplace,preco_br,data_captura,url_oferta,hash_local) "
    "VALUES (?,?,?,?,?,?,?)"
)
SQL_READ = (
    "SELECT evidence_id,produto,marketplace,preco_br,data_captura,url_oferta,hash_local "
    "FROM " + TABLE + " WHERE evidence_id=?"
)


def homolog_url_valid(raw):
    if not isinstance(raw, str):
        return False
    try:
        p = urlsplit(raw.strip())
        return (p.scheme in ("libsql", "https") and
                p.hostname == HOMOLOG_HOST and not p.username and
                not p.password and not p.port and not p.path.strip("/") and
                not p.query and not p.fragment)
    except ValueError:
        return False


def source_path():
    return Path.home() / ".local" / "share" / "mkt-rss" / "price_evidence.sqlite"


def _valid_row(row):
    produto, marketplace, preco, data, url, local_hash = row
    if not all(isinstance(v, str) and v for v in row):
        return False
    if marketplace != "shopee" or len(produto) > 500:
        return False
    if not re.fullmatch(r"R\$ (?:\d{1,3}(?:\.\d{3})*|\d+),\d{2}", preco):
        return False
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
        return False
    try:
        from datetime import datetime
        datetime.strptime(data, "%d/%m/%Y")
        host = urlsplit(url).hostname
        if (urlsplit(url).scheme != "https" or
                host not in ("shopee.com.br", "www.shopee.com.br")):
            return False
    except (ValueError, TypeError):
        return False
    original = "|".join((produto, marketplace, preco, data, url))
    return local_hash == hashlib.sha256(original.encode("utf-8")).hexdigest()[:16]


def load_local(path=None):
    """Return [tuple of 7 values]; do not create or mutate local database."""
    path = Path(path) if path is not None else source_path()
    if path.is_symlink() or not path.is_file():
        raise ValueError("LOCAL_EVIDENCE_MISSING_OR_LINKED")
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("PRAGMA query_only=ON")
        rows = conn.execute(
            "SELECT produto,marketplace,preco_br,data_captura,url_oferta,hash_evidencia "
            "FROM price_evidence WHERE marketplace='shopee' ORDER BY id"
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        raise ValueError("NO_LOCAL_SHOPEE_EVIDENCE")
    output = []
    for row in rows:
        if not _valid_row(row):
            raise ValueError("INVALID_LOCAL_EVIDENCE")
        canonical = "\x1f".join(row)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        output.append((digest,) + row)
    return output


def sync(rows, execute, apply=False):
    """Uses existing cloud_db.turso_execute. A verified readback is mandatory.

    With apply=False this is a read-only reconciliation of remote records.
    Unknown remote failures return explicit status, never mark as synchronized.
    """
    if not rows:
        return {"ok": False, "reason": "NO_EVIDENCE"}
    if apply:
        created = execute(SQL_CREATE)
        if not isinstance(created, dict) or "erro" in created:
            return {"ok": False, "reason": "REMOTE_SCHEMA_FAILED"}
    inserted = 0
    verified = 0
    for row in rows:
        if apply:
            write = execute(SQL_INSERT, row)
            if not isinstance(write, dict) or "erro" in write:
                return {"ok": False, "reason": "REMOTE_WRITE_UNKNOWN_RECONCILE",
                        "verified": verified}
            inserted += int(write.get("affected") or 0)
        read = execute(SQL_READ, (row[0],))
        if not isinstance(read, dict) or "erro" in read:
            return {"ok": False, "reason": "REMOTE_READ_FAILED", "verified": verified}
        values = read.get("rows") or []
        if len(values) != 1 or tuple(values[0]) != tuple(row):
            return {"ok": False, "reason": "REMOTE_READBACK_MISMATCH",
                    "verified": verified}
        verified += 1
    return {"ok": True, "total_local": len(rows),
            "new_remote_rows": inserted, "exact_readback": verified}
