"""Opt-in durable editorial trace outbox using the existing Turso HTTP client.

Never enables a connection, creates a table, or writes without explicit
allowlisted host and credentials. Do NOT use this module to approve posts.
"""
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit

from mkt_flow_p0.cloud_db import turso_enabled, turso_execute
from mkt_flow_p0.editorial_trace import SCHEMA, json_trace


def _host():
    url = (os.getenv("TURSO_DATABASE_URL") or "").strip()
    if url.startswith("libsql://"):
        url = "https://" + url[len("libsql://"):]
    try:
        return urlsplit(url).hostname or ""
    except ValueError:
        return ""


def _allowed():
    # Exact match: do not accidentally write production or wrong workspace.
    expected = os.getenv("CONEXO_TRACE_TURSO_ALLOWED_HOST", "").strip()
    return bool(expected and expected == _host() and turso_enabled())


def save_turso_trace(packet, *, execute=turso_execute):
    """Store exactly one versioned, private metadata-only envelope.

    Returns stable reason strings; never retries unknown writes, and never
    saves article bodies or prompts. Database permissions are enforced by
    Turso token; caller must store it only in a secret manager.
    """
    if not _allowed():
        return {"ok": False, "reason": "TRACE_STORAGE_NOT_CONFIGURED"}
    # Validate all required metadata BEFORE creating a table or writing data.
    if (not isinstance(packet, dict) or packet.get("schema") != SCHEMA
            or packet.get("publication_authorized") is not False
            or not isinstance(packet.get("run_id"), str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", packet["run_id"])
            or not isinstance(packet.get("article_id"), str)
            or not 1 <= len(packet["article_id"]) <= 128
            or not isinstance(packet.get("content_sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", packet["content_sha256"])
            or type(packet.get("post_id")) not in (int, type(None))
            or (type(packet.get("post_id")) is int and packet["post_id"] <= 0)
            or not isinstance(packet.get("events"), list)
            or not 1 <= len(packet["events"]) <= 64):
        return {"ok": False, "reason": "TRACE_INVALID"}
    out = execute("""CREATE TABLE IF NOT EXISTS conexo_editorial_trace_v1 (
        run_id TEXT PRIMARY KEY,
        article_id TEXT NOT NULL,
        post_id INTEGER,
        content_sha256 TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    if not isinstance(out, dict) or "erro" in out:
        return {"ok": False, "reason": "TRACE_SCHEMA_FAILED"}
    payload = json_trace(packet)
    if len(payload.encode("utf-8")) > 128 * 1024:
        return {"ok": False, "reason": "TRACE_TOO_LARGE"}
    result = execute("""INSERT INTO conexo_editorial_trace_v1
        (run_id,article_id,post_id,content_sha256,payload_json,created_at)
        VALUES (?,?,?,?,?,?)""", (
        packet["run_id"], packet["article_id"], packet["post_id"],
        packet["content_sha256"], payload,
        datetime.now(timezone.utc).isoformat()
    ))
    if not isinstance(result, dict) or "erro" in result:
        # Could be network timeout AFTER a committed INSERT: do not retry.
        return {"ok": False, "reason": "TRACE_INSERT_UNKNOWN_RECONCILE_BY_RUN_ID"}
    return {"ok": True, "run_id": packet["run_id"], "storage": "turso"}


def get_turso_trace(run_id, *, execute=turso_execute):
    if not _allowed():
        return {"ok": False, "reason": "TRACE_STORAGE_NOT_CONFIGURED"}
    if not isinstance(run_id, str) or not 8 <= len(run_id) <= 128:
        return {"ok": False, "reason": "TRACE_INVALID_ID"}
    result = execute(
        "SELECT payload_json FROM conexo_editorial_trace_v1 WHERE run_id = ?",
        (run_id,),
    )
    if not isinstance(result, dict) or "erro" in result:
        return {"ok": False, "reason": "TRACE_READ_FAILED"}
    rows = result.get("rows") or []
    if len(rows) != 1 or not rows[0]:
        return {"ok": False, "reason": "TRACE_NOT_FOUND"}
    try:
        packet = json.loads(rows[0][0])
    except (ValueError, TypeError):
        return {"ok": False, "reason": "TRACE_CORRUPT"}
    return {"ok": True, "trace": packet}
