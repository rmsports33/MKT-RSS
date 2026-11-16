#!/usr/bin/env python3
"""Minimal, opt-in Hostinger bridge to the *existing* MKT-RSS/Turso queue.

--snapshot: SQL SELECT only. --collect: bounded RSS discovery and queue insert;
never LLM, WP, publish, migrations or arbitrary commands. Credentials only on
Hostinger, from an owner-controlled private file, never from GitHub requests.
"""
import argparse
import json
import os
import stat
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CONFIG = Path.home() / ".config/conexo-os"
TOKEN_FILE = CONFIG / "turso-rss-writer.token"
URL_FILE = CONFIG / "turso-database-url"
MAX_ITEMS = 2
SOURCE = "tecnoblog"


def _fail(reason):
    print(json.dumps({"status": "BLOCKED", "reason": reason,
                      "wordpress_written": False, "publication_authorized": False}))
    return 2


def _read_private(path):
    """Require an owner-owned regular file, non-symlink, mode 0400/0600."""
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("PRIVATE_CONFIG_PERMISSIONS")
    if not (info.st_mode & stat.S_IRUSR) or info.st_size < 1 or info.st_size > 4096:
        raise ValueError("PRIVATE_CONFIG_SIZE_OR_MODE")
    data = path.read_text(encoding="utf-8").strip()
    if not data or "\n" in data or "\r" in data:
        raise ValueError("PRIVATE_CONFIG_VALUE")
    return data


def _trusted_turso_url(raw):
    if raw.startswith("libsql://"):
        raw = "https://" + raw[len("libsql://"):]
    parsed = urlsplit(raw)
    if (parsed.scheme != "https" or not parsed.hostname
            or not parsed.hostname.startswith("mkt-rss-")
            or not parsed.hostname.endswith(".turso.io")
            or "homolog" in parsed.hostname or parsed.username or parsed.password
            or parsed.port is not None or parsed.path not in ("", "/")
            or parsed.query or parsed.fragment):
        raise ValueError("TURSO_MAIN_ENDPOINT_REQUIRED")
    return "https://" + parsed.hostname


def _configure():
    # A configured DB URL may come from a protected environment or a private file.
    # The token NEVER comes from a GitHub request or ambient Cron environment.
    raw_url = os.environ.get("TURSO_DATABASE_URL", "").strip()
    if not raw_url:
        raw_url = _read_private(URL_FILE)
    db_url = _trusted_turso_url(raw_url)
    token = _read_private(TOKEN_FILE)
    os.environ["TURSO_DATABASE_URL"] = db_url
    os.environ["TURSO_AUTH_TOKEN"] = token
    os.environ["CONEXO_REQUIRE_CLOUD_PERSISTENCE"] = "1"
    # Critical: fila_pautas must verify the pre-existing Turso tables and must
    # never execute CREATE/ALTER/index DDL from this remotely-triggered collector.
    os.environ["CONEXO_RSS_SCHEMA_PREEXISTS"] = "1"
    os.environ["CONEXO_PRODUCT_LINKS_ENABLED"] = "0"
    # Explicitly disable all optional write/publication/LLM paths.
    for name in ("WP_USER", "WP_APP_PASSWORD", "CONEXO_WP_USER",
                 "CONEXO_WP_APP_PASSWORD", "GROQ_API_KEY",
                 "CONEXO_RSS_DRAFT", "CONEXO_RSS_DRAFT_STAGING",
                 "CONEXO_GATE_REMEDIATION_AUTO"):
        os.environ.pop(name, None)


def snapshot():
    from mkt_flow_p0 import cloud_db
    from mkt_flow_p0.fila_pautas import STATES
    # Never call fila_pautas.listar(): that helper runs init_queue() (DDL).
    result = cloud_db.turso_execute(
        "SELECT estado, COUNT(*) FROM rss_pautas GROUP BY estado")
    if "erro" in result:
        raise RuntimeError("TURSO_QUEUE_READ_FAILED")
    counts = {name: 0 for name in sorted(STATES)}
    for row in result.get("rows", []):
        if len(row) != 2 or row[0] not in STATES or type(row[1]) not in (str, int):
            raise RuntimeError("UNEXPECTED_QUEUE_SCHEMA")
        n = int(row[1])
        if n < 0:
            raise RuntimeError("UNEXPECTED_QUEUE_COUNT")
        counts[row[0]] = n
    return {"status": "PASS", "mode": "READ_ONLY", "counts": counts,
            "total": sum(counts.values()), "wordpress_written": False,
            "publication_authorized": False}


def collect():
    from rss_queue_collect import coletar
    # Existing single-writer lease, deduplication and Turso fail-closed rules
    # remain owned by fila_pautas.registrar().
    result = coletar(fonte=SOURCE, limite=MAX_ITEMS, dry_run=False)
    if not isinstance(result, dict):
        raise RuntimeError("INVALID_COLLECTOR_RESPONSE")
    failures = result.get("falhas") or []
    if not isinstance(failures, list):
        raise RuntimeError("INVALID_COLLECTOR_RESPONSE")
    return {"status": "PARTIAL" if failures else "PASS", "mode": "QUEUE_ONLY",
            "new": int(result.get("novas", 0)),
            "duplicates": int(result.get("duplicadas", 0)),
            "failures": len(failures), "wordpress_written": False,
            "publication_authorized": False}


def main(argv=None):
    p = argparse.ArgumentParser(description="MKT-RSS/Turso queue bridge (safe allowlist)")
    exclusive = p.add_mutually_exclusive_group(required=True)
    exclusive.add_argument("--snapshot", action="store_true")
    exclusive.add_argument("--collect", action="store_true")
    args = p.parse_args(argv)
    try:
        _configure()
        payload = snapshot() if args.snapshot else collect()
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, OverflowError):
        return _fail("QUEUE_BRIDGE_PRECONDITION_OR_OPERATION_FAILED")
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
