"""Probe restrito ao Turso de homologação. Sem RSS, WP ou dados reais."""
import argparse
import json
import os
import sys
from urllib.parse import urlsplit

from mkt_flow_p0 import cloud_db, fila_pautas

def guard():
    url = (os.getenv("TURSO_DATABASE_URL") or "").strip()
    token = (os.getenv("TURSO_AUTH_TOKEN") or "").strip()
    host = urlsplit(url.replace("libsql://", "https://", 1)).hostname or ""
    if not token:
        raise RuntimeError("Bloqueado: TURSO_AUTH_TOKEN vazio ou indisponível")
    if host != "mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io":
        raise RuntimeError("Bloqueado: TURSO_DATABASE_URL não corresponde ao hostname exato de homologação")
    if not cloud_db.turso_enabled():
        raise RuntimeError("Bloqueado: conexão remota Turso ausente")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=("seed", "verify"))
    ap.add_argument("--case", required=True, help="Identificador aleatório não sensível")
    args = ap.parse_args()
    guard()
    if not (8 <= len(args.case) <= 64 and all(c.isalnum() or c == "-" for c in args.case)):
        raise RuntimeError("Identificador inválido")
    item = {"fonte": "rss-queue-homolog", "titulo": "Prova RSS homologacao " + args.case,
            "link": "https://example.org/rss-homolog/" + args.case,
            "published": "2026-10-27"}
    if args.phase == "seed":
        got = fila_pautas.registrar(item)
        if not got["novo"]:
            raise RuntimeError("Seed já existente: use um case novo")
        print(json.dumps({"phase": "seed", "new": True, "id": got["id"]}))
    else:
        got = fila_pautas.registrar(item)
        if got["novo"]:
            raise RuntimeError("Falha: segunda execução inseriu duplicata")
        found = fila_pautas.listar(limite=100)
        if not any(p["id"] == got["id"] for p in found):
            raise RuntimeError("Falha: registro não está persistido")
        print(json.dumps({"phase": "verify", "duplicate": True, "persisted": True, "id": got["id"]}))

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("HOMOLOG_FAIL:", str(exc), file=sys.stderr)
        raise SystemExit(1)
