#!/usr/bin/env python3
"""Turso homolog sync of existing Shopee price evidence; no Shopee secrets."""
import argparse
import getpass
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mkt_flow_p0.price_evidence_turso import homolog_url_valid, load_local, sync


def main(argv=None):
    parser = argparse.ArgumentParser(description="Shopee SQLite -> Turso homolog only")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true", help="Local-only validation; no network")
    modes.add_argument("--apply", action="store_true", help="Insert in homolog and read back")
    modes.add_argument("--verify", action="store_true", help="Independent readback in homolog")
    args = parser.parse_args(argv)
    try:
        rows = load_local()
    except (ValueError, OSError, sqlite3.DatabaseError) as e:
        print(json.dumps({"ok": False, "reason": type(e).__name__ + ": " + str(e)}))
        return 1
    if args.check:
        print(json.dumps({"ok": True, "local_records": len(rows),
                          "remote_write": False, "ids": [row[0][:12] for row in rows]}))
        return 0
    if not (sys.stdin.isatty() and sys.stderr.isatty()):
        print("BLOQUEADO: terminal interativo obrigatorio para token Turso")
        return 2
    url = input("URL do banco Turso mkt-rss-homolog (sem token): ").strip()
    if not homolog_url_valid(url):
        print("BLOQUEADO: destino deve ser EXCLUSIVAMENTE o Turso mkt-rss-homolog")
        return 2
    token = getpass.getpass("Token individual mkt-rss-homolog (oculto): ").strip()
    if not token:
        print("BLOQUEADO: token vazio")
        return 2
    # Do not print or persist token. Only this process receives the variables.
    old_url = os.environ.get("TURSO_DATABASE_URL")
    old_token = os.environ.get("TURSO_AUTH_TOKEN")
    try:
        os.environ["TURSO_DATABASE_URL"] = url
        os.environ["TURSO_AUTH_TOKEN"] = token
        del token
        from mkt_flow_p0.cloud_db import turso_execute
        result = sync(rows, turso_execute, apply=args.apply)
    finally:
        if old_url is None:
            os.environ.pop("TURSO_DATABASE_URL", None)
        else:
            os.environ["TURSO_DATABASE_URL"] = old_url
        if old_token is None:
            os.environ.pop("TURSO_AUTH_TOKEN", None)
        else:
            os.environ["TURSO_AUTH_TOKEN"] = old_token
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    import sqlite3
    sys.exit(main())
