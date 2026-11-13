"""Reconciliação segura: catálogo GitHub contra fila Turso, sem escrita.

Não imprime títulos, URLs, IDs internos de pauta nem credenciais.
"""
import json
import os
from collections import Counter
from urllib.parse import urlsplit
from mkt_flow_p0.cloud_db import turso_execute
from mkt_flow_p0.product_catalog import load, identify_in_headline

PAGE = 200
MAX_ROWS = 50000
STATES = {"DESCOBERTA", "SELECIONADA", "EM_PRODUCAO", "EM_REVISAO",
          "CONCLUIDA", "REJEITADA", "BLOQUEADA"}

def reconcile(fetch=turso_execute, catalog=None):
    catalog = catalog or load()
    products = {p["id"]: {"pautas": 0, "estados": Counter()} for p in catalog["products"]}
    summary = {"schema": "conexo-catalog-reconciliation/1", "mode": "READ_ONLY",
               "total_rows": 0, "unmatched_rows": 0, "ambiguous_rows": 0,
               "duplicate_product_pauta_candidates": 0, "products": products}
    offset = 0
    while True:
        if offset >= MAX_ROWS:
            raise RuntimeError("AUDIT_LIMIT_EXCEEDED")
        response = fetch("SELECT titulo, estado FROM rss_pautas ORDER BY id LIMIT ? OFFSET ?",
                         (min(PAGE, MAX_ROWS-offset), offset))
        if response.get("erro"):
            raise RuntimeError("TURSO_READ_FAILED") from None
        rows = response.get("rows")
        if not isinstance(rows, list):
            raise RuntimeError("TURSO_ROWS_INVALID")
        if not rows:
            break
        for row in rows:
            if not isinstance(row, list) or len(row) != 2 or not isinstance(row[0], str):
                raise RuntimeError("TURSO_ROW_SCHEMA_INVALID")
            title, state = row
            if state not in STATES:
                raise RuntimeError("UNKNOWN_EDITORIAL_STATE")
            found = identify_in_headline(title, catalog)
            summary["total_rows"] += 1
            if found["status"] == "CANDIDATE_MATCH":
                item = products[found["product_id"]]
                item["pautas"] += 1
                item["estados"][state] += 1
            elif found["status"] == "REVIEW":
                summary["ambiguous_rows"] += 1
            else:
                summary["unmatched_rows"] += 1
        offset += len(rows)
        if len(rows) < PAGE:
            break
    for value in products.values():
        if value["pautas"] > 1:
            summary["duplicate_product_pauta_candidates"] += value["pautas"] - 1
        value["estados"] = dict(sorted(value["estados"].items()))
    summary["products_with_pautas"] = sum(v["pautas"] > 0 for v in products.values())
    summary["products_without_pautas"] = len(products)-summary["products_with_pautas"]
    summary["requires_editorial_review"] = True
    summary["wordpress_status_verified"] = False
    summary["queue_modified"] = False
    return summary

def main():
    raw = os.getenv("TURSO_DATABASE_URL", "").strip()
    host = urlsplit(raw.replace("libsql://", "https://", 1)).hostname
    if not raw or not host or not host.endswith(".turso.io") or not os.getenv("TURSO_AUTH_TOKEN", "").strip():
        raise SystemExit("BLOCKED: existing repository Turso credentials missing or invalid host")
    try:
        result = reconcile()
    except (RuntimeError, ValueError, TypeError, KeyError):
        raise SystemExit("BLOCKED: authenticated read-only audit failed (no query details exposed)") from None
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
