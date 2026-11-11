"""Offline SQLite recovery without a resident executor. No credentials in manifest.

Not a Turso backup: that service needs its own authenticated export. Never expose
editorial snapshots in public Actions artifacts. SHA detects corruption, not trust.
"""
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def export_queue(source, target):
    source, target = Path(source).resolve(), Path(target).resolve()
    if not source.is_file() or target.exists():
        raise ValueError("origem inexistente ou destino ja existe")
    manifest = target.with_suffix(target.suffix + ".json")
    if manifest.exists():
        raise ValueError("manifesto ja existe")
    # Source read-only; SQLite backup includes committed WAL contents coherently.
    with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as src:
        os.close(os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
        with sqlite3.connect(target) as dest:
            src.backup(dest)
            if dest.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("snapshot inconsistente")
    report = {"schema": "conexo-queue-snapshot/1", "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
              "created_at": datetime.now(timezone.utc).isoformat(), "kind": "sqlite", "private": True}
    with manifest.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return report


def restore_queue(snapshot, target, manifest):
    snapshot, target = Path(snapshot).resolve(), Path(target).resolve()
    if target.exists() or not snapshot.is_file():
        raise ValueError("restauracao nao sobrescreve estado existente")
    data = json.loads(Path(manifest).read_text(encoding="utf-8"))
    if data.get("schema") != "conexo-queue-snapshot/1" or data.get("sha256") != hashlib.sha256(snapshot.read_bytes()).hexdigest():
        raise ValueError("snapshot corrompido ou manifesto invalido")
    with sqlite3.connect(snapshot.as_uri() + "?mode=ro", uri=True) as src:
        if src.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("snapshot inconsistente")
        os.close(os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
        with sqlite3.connect(target) as dest:
            src.backup(dest)
    return {"status": "RESTAURADO", "sha256_snapshot": data["sha256"], "wordpress_alterado": False}
