"""Prova concorrente exclusivamente no banco Turso de homologação."""
import argparse
import json
import os
import time
from mkt_flow_p0 import cloud_db, fila_pautas
from scripts.rss_queue_turso_homolog_probe import guard

def exec_sql(sql, args=()):
    r = cloud_db.turso_execute(sql, args)
    if "erro" in r:
        raise RuntimeError("Turso homolog: " + r["erro"])
    return r

def item(case, worker):
    return {"fonte": "homolog", "titulo": "Concorrencia RSS de homologacao " + case,
            "link": "https://example.org/rss-concurrency/" + case + "/" + worker,
            "published": "2026-10-28"}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("phase", choices=["worker", "check"])
    p.add_argument("--case", required=True)
    p.add_argument("--worker", choices=["a", "b"])
    a = p.parse_args()
    guard()
    if not (a.case.startswith("pr28-") and a.case[5:].isdigit()):
        raise RuntimeError("case inválido")
    exec_sql("""CREATE TABLE IF NOT EXISTS rss_homolog_barrier
                 (case_id TEXT, worker TEXT, PRIMARY KEY(case_id, worker))""")
    if a.phase == "worker":
        if not a.worker:
            raise RuntimeError("worker necessário")
        exec_sql("INSERT OR IGNORE INTO rss_homolog_barrier VALUES (?,?)", (a.case, a.worker))
        deadline = time.monotonic() + 65
        while time.monotonic() < deadline:
            rows = exec_sql("SELECT COUNT(*) FROM rss_homolog_barrier WHERE case_id=?",
                            (a.case,))["rows"]
            if int(rows[0][0]) == 2:
                break
            time.sleep(1)
        else:
            raise RuntimeError("barreira expirou sem dois runners")
        try:
            r = fila_pautas.registrar(item(a.case, a.worker))
            print(json.dumps({"worker": a.worker, "novo": r["novo"],
                              "motivo": r.get("motivo", "")}))
        except RuntimeError as exc:
            if "ocupada por outro coletor" not in str(exc):
                raise
            print(json.dumps({"worker": a.worker, "bloqueado_por_concorrencia": True}))
    else:
        import hashlib
        from mkt_flow_p0.fila_pautas import _url
        ids = [hashlib.sha256(_url(item(a.case, w)["link"]).encode()).hexdigest()[:32]
               for w in ("a", "b")]
        rows = exec_sql("SELECT id FROM rss_pautas WHERE id IN (?,?)", tuple(ids))["rows"]
        print(json.dumps({"count": len(rows), "ids": [r[0] for r in rows]}))
        if len(rows) != 1:
            raise RuntimeError("Concorrência produziu quantidade inesperada de registros")
        print("TURSO_CONCURRENT_PASS")

if __name__ == "__main__":
    main()
