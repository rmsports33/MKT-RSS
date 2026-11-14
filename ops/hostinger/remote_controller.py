#!/usr/bin/env python3
"""Fail-closed read-only / review-only remote operations controlled via GitHub.

The GitHub file is a request, NOT executable code. Only an explicit action
allowlist is supported. No WordPress or Turso credentials and no publication.
"""
import fcntl
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "mkt-rss-runner"
STATE = Path.home() / ".local/state/conexo-os"
LAUNCHER = ROOT / "ops/hostinger/conexo_editorial.sh"
ALLOWED = {
    "image_technical_check": ["--image-check"],
    "binance_image_review_package": ["--image-stage", "--import-binance-image"],
    "binance_substantive_review": ["--import-binance-reviewed"],
}
REPOSITORY = "https://github.com/rmsports33/MKT-RSS.git"
BRANCH = "feat/hostinger-runtime-independente-20261113"


def invoke(argv, timeout=120):
    r = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout,
                       env={k:v for k,v in os.environ.items() if k not in {
                           "GROQ_API_KEY", "WP_USER", "WP_APP_PASSWORD",
                           "CONEXO_WP_USER", "CONEXO_WP_APP_PASSWORD", "TURSO_AUTH_TOKEN"
                       }})
    if r.returncode:
        return {"status":"FAILED","exit_code":r.returncode,
                "output":(r.stdout+"\n"+r.stderr)[-3000:]}
    return {"status":"PASS","exit_code":0, "output":r.stdout[-3000:]}


def main():
    if not LAUNCHER.is_file() or LAUNCHER.is_symlink():
        raise SystemExit("BLOCKED: trusted local launcher missing")
    # Execute exactly the checked-out code. The cron does NOT pull updates:
    # only the operator can update the trusted checkout.
    remote = subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT,
                            text=True, capture_output=True, timeout=10)
    if remote.returncode or remote.stdout.strip() not in {REPOSITORY, REPOSITORY.removesuffix(".git")}:
        raise SystemExit("BLOCKED: unexpected repository origin")
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(STATE, 0o700)
    os.umask(0o077)
    with (STATE/"remote-control.lock").open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        fetched = subprocess.run(
            ["git","fetch","--no-tags","origin","refs/heads/"+BRANCH],
            cwd=ROOT,capture_output=True,text=True,timeout=45)
        if fetched.returncode:
            raise SystemExit("BLOCKED: remote request fetch failed")
        requested = subprocess.run(
            ["git","show","FETCH_HEAD:ops/hostinger/remote_request.json"],
            cwd=ROOT,capture_output=True,text=True,timeout=15)
        if requested.returncode:
            raise SystemExit("BLOCKED: remote request missing on trusted branch")
        data = json.loads(requested.stdout)
        if not isinstance(data,dict) or set(data)!={"schema","job_id","action","article_ref"}:
            raise SystemExit("BLOCKED: invalid remote request")
        if data["schema"]!="conexo-remote-request/1" or data["article_ref"]!="binance-revisao-6e8da0b05713":
            raise SystemExit("BLOCKED: unsupported request")
        jid=data["job_id"]
        if not isinstance(jid,str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{7,79}",jid):
            raise SystemExit("BLOCKED: invalid job id")
        action=data["action"]
        if action not in ALLOWED:
            raise SystemExit("BLOCKED: action not on allowlist")
        receipt=STATE/"remote-control-receipt.json"
        prev=json.loads(receipt.read_text()) if receipt.is_file() else {}
        if prev.get("job_id")==jid:
            print(json.dumps({"status":"ALREADY_PROCESSED","job_id":jid,
                              "last_run_status":prev.get("status"),
                              "steps":[{"step":v.get("step"),"status":v.get("status")}
                                       for v in prev.get("results",[])],
                              "receipt":str(receipt)}))
            return
        # Commit STARTED before any action; do not retry on failure/crash.
        def record(info):
            temp=STATE/"remote-control-receipt.tmp"
            temp.write_text(json.dumps(info,ensure_ascii=False,indent=2)+"\n")
            os.chmod(temp,0o600)
            os.replace(temp,receipt)
        entry={"schema":"conexo-remote-receipt/1","job_id":jid,"action":action,
               "started_utc":datetime.now(timezone.utc).isoformat(),
               "status":"STARTED","wordpress_written":False,"publication_authorized":False}
        record(entry)
        outcomes=[]
        for flag in ALLOWED[action]:
            result=invoke(["bash",str(LAUNCHER),flag], timeout=120)
            outcomes.append({"step":flag,**result})
            if result["status"]!="PASS":
                break
        entry.update(status="PASS" if len(outcomes)==len(ALLOWED[action]) and all(
            x["status"]=="PASS" for x in outcomes) else "FAILED",
            completed_utc=datetime.now(timezone.utc).isoformat(),
            results=outcomes)
        record(entry)
        print(json.dumps({"job_id":jid,"status":entry["status"],
                          "steps":len(outcomes),"receipt":str(receipt)}))

if __name__=="__main__":
    main()
