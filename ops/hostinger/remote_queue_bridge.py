#!/usr/bin/env python3
"""Minimal, opt-in Hostinger bridge to the existing MKT-RSS/Turso queue.

--snapshot: SQL SELECT only. --collect: bounded RSS discovery and queue insert;
never LLM, WP, publish, migrations or arbitrary commands. Credentials stay on
Hostinger: URL from the existing private rss-queue.env, token from the existing
private writer-token file. No shell evaluation of configuration.
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
ENV_FILE = CONFIG / "rss-queue.env"
TOKEN_FILE = CONFIG / "turso-rss-writer.token"
MAX_ITEMS = 2
SOURCE = "tecnoblog"


def _fail(reason):
    print(json.dumps({"status": "BLOCKED", "reason": reason,
                      "wordpress_written": False, "publication_authorized": False}))
    return 2


def _read_private(path):
    """Require an owner-owned regular file, non-symlink, private mode."""
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("PRIVATE_CONFIG_PERMISSIONS")
    if not (info.st_mode & stat.S_IRUSR) or info.st_size < 1 or info.st_size > 4096:
        raise ValueError("PRIVATE_CONFIG_SIZE_OR_MODE")
    data = path.read_text(encoding="utf-8").strip()
    if not data or "\n" in data or "\r" in data:
        raise ValueError("PRIVATE_CONFIG_VALUE")
    return data


def _read_env_config(path):
    """Parse the existing private .env as data; never source/evaluate shell code."""
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o600 or info.st_size < 1
            or info.st_size > 16384):
        raise ValueError("RSS_ENV_FILE_PERMISSIONS_OR_SIZE")
    # Parse only the two required keys as plain data. Never evaluate shell,
    # interpolation, command substitution, or arbitrary dotenv expressions.
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        if raw.startswith("export "):
            raw = raw[7:].lstrip()
        key, separator, value = raw.partition("=")
        if not separator:
            continue
        key = key.strip()
        if key not in ("TURSO_DATABASE_URL", "CONEXO_RSS_TARGET_DB"):
            continue
        if key in values:
            raise ValueError("RSS_ENV_DUPLICATE_KEY")
        value = value.strip()
        if value[:1] in ("'", '"'):
            quote = value[0]
            end = value.find(quote, 1)
            if end < 0:
                raise ValueError("RSS_ENV_INVALID_QUOTING")
            trailing = value[end + 1:].strip()
            if trailing and not trailing.startswith("#"):
                raise ValueError("RSS_ENV_INVALID_TRAILING_DATA")
            value = value[1:end]
        else:
            value = value.split(" #", 1)[0].strip()
        values[key] = value
    return values


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
    # Reuse the URL and explicit production target already maintained by the
    # existing Hostinger queue runner. The token is read from its private file.
    config = _read_env_config(ENV_FILE)
    raw_url = os.environ.get("TURSO_DATABASE_URL", "").strip()
    if not raw_url:
        raw_url = str(config.get("TURSO_DATABASE_URL") or "").strip()
    target = (os.environ.get("CONEXO_RSS_TARGET_DB")
              or config.get("CONEXO_RSS_TARGET_DB") or "").strip()
    if target != "mkt-rss":
        raise ValueError("EXPLICIT_MAIN_DATABASE_TARGET_REQUIRED")
    db_url = _trusted_turso_url(raw_url)
    token = _read_private(TOKEN_FILE)
    os.environ["TURSO_DATABASE_URL"] = db_url
    os.environ["TURSO_AUTH_TOKEN"] = token
    os.environ["CONEXO_RSS_TARGET_DB"] = "mkt-rss"
    os.environ["CONEXO_REQUIRE_CLOUD_PERSISTENCE"] = "1"
    # Critical: fila_pautas verifies pre-existing tables and never executes DDL.
    os.environ["CONEXO_RSS_SCHEMA_PREEXISTS"] = "1"
    # Queue intake only; optional catalog links are deliberately disabled.
    os.environ["CONEXO_PRODUCT_LINKS_ENABLED"] = "0"
    # Explicitly disable optional write/publication/LLM paths.
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


def list_titles():
    """Read-only, bounded index of DESCOBERTA pautas for human triage.

    Fixed SELECT with a constant state filter and LIMIT. No user input is ever
    interpolated into SQL. Returns editorial metadata only (id/titulo/fonte/
    estado/pontuacao/publicada_em) — no resumo, no URLs, no credentials, no
    article text. Never writes WordPress/Turso and never authorizes publication.
    """
    from mkt_flow_p0 import cloud_db
    from mkt_flow_p0.fila_pautas import STATES
    if "DESCOBERTA" not in STATES:
        raise RuntimeError("UNEXPECTED_QUEUE_SCHEMA")
    result = cloud_db.turso_execute(
        "SELECT id, titulo, fonte, estado, pontuacao, publicada_em "
        "FROM rss_pautas WHERE estado = 'DESCOBERTA' "
        "ORDER BY created_at DESC LIMIT 20")
    if "erro" in result:
        raise RuntimeError("TURSO_QUEUE_READ_FAILED")
    rows = []
    for row in result.get("rows", []):
        if len(row) != 6:
            raise RuntimeError("UNEXPECTED_QUEUE_SCHEMA")
        pid, titulo, fonte, estado, pontuacao, publicada = row
        if (not isinstance(pid, str) or not isinstance(titulo, str)
                or not isinstance(fonte, str) or estado != "DESCOBERTA"):
            raise RuntimeError("UNEXPECTED_QUEUE_SCHEMA")
        rows.append({
            "id": pid[:32],
            "titulo": titulo[:300],
            "fonte": fonte[:60],
            "estado": estado,
            "pontuacao": int(pontuacao) if str(pontuacao).lstrip("-").isdigit() else 0,
            "publicada_em": publicada if isinstance(publicada, str) else None,
        })
    return {"status": "PASS", "mode": "READ_ONLY", "state": "DESCOBERTA",
            "count": len(rows), "items": rows, "wordpress_written": False,
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
    exclusive.add_argument("--list", action="store_true")
    exclusive.add_argument("--collect", action="store_true")
    args = p.parse_args(argv)
    try:
        _configure()
        if args.snapshot:
            payload = snapshot()
        elif args.list:
            payload = list_titles()
        else:
            payload = collect()
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, OverflowError):
        return _fail("QUEUE_BRIDGE_PRECONDITION_OR_OPERATION_FAILED")
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
