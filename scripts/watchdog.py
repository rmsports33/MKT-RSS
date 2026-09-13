#!/usr/bin/env python3
"""
scripts/watchdog.py — verifica saúde do cron diário (pode rodar local ou no cron-job.org via API).

Uso local:
  python scripts/watchdog.py --repo rmsports33/MKT-RSS --token $GITHUB_TOKEN
  python scripts/watchdog.py --repo rmsports33/MKT-RSS --token $GITHUB_TOKEN --disparar

Sem --disparar, só relata. Com --disparar, chama workflow_dispatch se o último
run estiver há >20h ou falhou.
"""
import argparse
import json
import sys
from datetime import datetime, timezone

import requests


def ultimo_run(repo: str, token: str, workflow: str = "daily.yml", timeout: int = 15) -> dict:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
               "User-Agent": "MKT-Flow-watchdog"}
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/runs?per_page=1"
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        runs = (r.json().get("workflow_runs") or [])
        return runs[0] if runs else {"erro": "nenhum run ainda"}
    except requests.Timeout:
        return {"erro": f"timeout após {timeout}s"}
    except Exception as e:
        try:
            detail = r.text[:150]  # type: ignore
        except Exception:
            detail = str(e)[:150]
        return {"erro": f"API falhou: {detail}"}


def disparar(repo: str, token: str, workflow: str = "daily.yml", ref: str = "master", timeout: int = 15) -> dict:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches"
    try:
        r = requests.post(url, headers=headers, json={"ref": ref}, timeout=timeout)
        if r.status_code in (201, 204):
            return {"ok": True, "status": r.status_code}
        return {"ok": False, "status": r.status_code, "erro": r.text[:150]}
    except Exception as e:
        return {"ok": False, "erro": str(e)[:150]}


def main():
    ap = argparse.ArgumentParser(description="Watchdog do cron diário")
    ap.add_argument("--repo", required=True, help="owner/repo, ex: rmsports33/MKT-RSS")
    ap.add_argument("--token", required=True, help="PAT com escopo repo (ou GITHUB_TOKEN)")
    ap.add_argument("--workflow", default="daily.yml")
    ap.add_argument("--ref", default="master")
    ap.add_argument("--disparar", action="store_true", help="dispara se >20h ou falha")
    args = ap.parse_args()

    info = ultimo_run(args.repo, args.token, args.workflow)
    if "erro" in info:
        print(json.dumps(info, ensure_ascii=False))
        sys.exit(2)
    status = info.get("conclusion") or info.get("status")
    updated = info.get("updated_at") or info.get("created_at") or ""
    try:
        dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        horas = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    except Exception:
        horas = 999
    rel = {"workflow": args.workflow, "status": status, "updated_at": updated,
           "horas_desde_ultimo": round(horas, 1), "url": info.get("html_url", "")}
    print(json.dumps(rel, ensure_ascii=False))
    if args.disparar and (horas > 20 or status in ("failure", "timed_out", "cancelled")):
        res = disparar(args.repo, args.token, args.workflow, args.ref)
        print(json.dumps({"disparo": res}, ensure_ascii=False))
        sys.exit(0 if res.get("ok") else 3)


if __name__ == "__main__":
    main()
