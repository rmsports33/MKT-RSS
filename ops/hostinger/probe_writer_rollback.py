#!/usr/bin/env python3
"""Prova autorizada de INSERT em Turso real dentro de ROLLBACK.

- NÃO publica / não chama WordPress / não atualiza esquema.
- Única tabela temporariamente afetada: rss_pautas
- A transação deve ser revertida e comprovada por leitura externa.
- Executar com token restrito, sem gravá-lo na linha de comando.
"""
import json
import os
import secrets
import sys
from pathlib import Path
from urllib.parse import urlparse

# Running a file under ops/hostinger does not automatically place the repo root
# on sys.path. Resolve it explicitly without relying on the caller's cwd.
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import requests


def _fail(reason):
    print(json.dumps({"status": "BLOCKED", "reason": reason, "publication_authorized": False}))
    return 2


def _step(resp):
    if not isinstance(resp, dict) or resp.get("type") != "ok":
        raise RuntimeError("SQL_STEP_FAILED")
    return ((resp.get("response") or {}).get("result") or {})


def main():
    if os.getenv("CONEXO_RSS_PERMISSIONS_PROBE") != "YES_ROLLBACK_ONLY":
        return _fail("EXPLICIT_ROLLBACK_PROBE_OPT_IN_REQUIRED")
    from mkt_flow_p0 import cloud_db
    if not cloud_db.turso_enabled():
        return _fail("CLOUD_CREDENTIALS_REQUIRED")
    url = os.environ["TURSO_DATABASE_URL"].strip()
    if url.startswith("libsql://"):
        url = "https://" + url[len("libsql://"):]
    parsed = urlparse(url)
    if (parsed.scheme != "https" or parsed.username or parsed.password or parsed.port
            or not parsed.hostname or not parsed.hostname.endswith(".turso.io")
            or not parsed.hostname.startswith("mkt-rss-") or "homolog" in parsed.hostname
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        return _fail("MAIN_DB_URL_REQUIRED")
    marker = "conexo-rollback-" + secrets.token_hex(12)
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    # The role has data_add for rss_pautas. No schema changes, no UPDATE/DELETE.
    sql = ("INSERT INTO rss_pautas "
           "(id, fonte, url, titulo, titulo_norm, publicada_em, resumo, estado, "
           "pontuacao, motivo, created_at, updated_at) "
           "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)")
    args = [marker, "ROLLBACK_TEST", "https://example.com/conexo/" + marker,
            "Teste temporário de transação reversível", "teste temporario de transacao reversivel",
            now, "", "DESCOBERTA", 10, "ROLLBACK_ONLY", now, now]

    def arg(v):
        return {"type": "text", "value": v} if isinstance(v, str) else {
            "type": "integer", "value": str(v)}

    requests_payload = {"requests": [
        {"type": "execute", "stmt": {"sql": "BEGIN"}},
        {"type": "execute", "stmt": {"sql": sql, "args": [arg(a) for a in args]}},
        {"type": "execute", "stmt": {"sql": "SELECT COUNT(*) FROM rss_pautas WHERE id=?",
                                       "args": [arg(marker)]}},
        {"type": "execute", "stmt": {"sql": "ROLLBACK"}},
        {"type": "close"}
    ]}
    # The server processes the entire pipeline sequentially on one connection.
    # Closing on an error prevents a pending transaction from being committed later.
    try:
        resp = requests.post(url.rstrip("/") + "/v2/pipeline",
            headers={"Authorization": "Bearer " + os.environ["TURSO_AUTH_TOKEN"].strip(),
                     "Content-Type": "application/json"},
            json=requests_payload, timeout=20, allow_redirects=False)
        if resp.status_code != 200:
            return _fail("DATABASE_HTTP_" + str(resp.status_code))
        body = resp.json()
        result = body.get("results") or []
        if len(result) != 5:
            return _fail("UNEXPECTED_PIPELINE_RESPONSE")
        for i in (0, 1, 2, 3):
            _step(result[i])
        rows = _step(result[2]).get("rows") or []
        observed = str(rows[0][0].get("value", "")) if rows and rows[0] else ""
        if observed != "1":
            return _fail("TRANSACTION_INSERT_NOT_OBSERVED")
        # Readback must be on a NEW connection to prove ROLLBACK.
        check = cloud_db.turso_execute(
            "SELECT COUNT(*) FROM rss_pautas WHERE id=?", (marker,))
        if "erro" in check:
            return _fail("READBACK_UNAVAILABLE")
        persisted = check.get("rows") or []
        if not persisted or str(persisted[0][0]) != "0":
            return _fail("ROLLBACK_NOT_PROVEN")
        print(json.dumps({"status": "PASS", "proof": "INSERT_WITH_ROLLBACK",
                          "persisted_test_rows": 0, "wordpress_modified": False,
                          "publication_authorized": False}))
        return 0
    except (requests.RequestException, ValueError, KeyError, TypeError, RuntimeError):
        return _fail("PROBE_FAILED_NO_SUCCESS_ASSERTION")


if __name__ == "__main__":
    sys.exit(main())
