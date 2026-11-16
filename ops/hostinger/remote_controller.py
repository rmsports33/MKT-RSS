#!/usr/bin/env python3
"""Fail-closed GitHub-request-controlled operations on the trusted Hostinger checkout.

GitHub requests are *data*, never executable code. Queue actions are opt-in,
limited to Turso snapshot / bounded RSS collection, with no WP or publication.
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
QUEUE_BRIDGE = ROOT / "ops/hostinger/remote_queue_bridge.py"
ALLOWED = {
    "image_technical_check": ["--image-check"],
    "binance_image_review_package": ["--image-stage", "--import-binance-image"],
    "binance_substantive_review": ["--import-binance-reviewed"],
    "queue_snapshot": ["--snapshot"],
    "queue_collect": ["--collect"],
}
QUEUE_ACTIONS = frozenset({"queue_snapshot", "queue_collect"})
REPOSITORY = "https://github.com/rmsports33/MKT-RSS.git"
BRANCH = "feat/hostinger-runtime-independente-20261113"


def validate_request(data):
    if not isinstance(data, dict) or set(data) != {"schema", "job_id", "action", "article_ref"}:
        raise ValueError("invalid remote request")
    if data["schema"] != "conexo-remote-request/1":
        raise ValueError("invalid schema")
    jid = data["job_id"]
    if not isinstance(jid, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{7,79}", jid):
        raise ValueError("invalid job id")
    action = data["action"]
    if action not in ALLOWED:
        raise ValueError("action not on allowlist")
    expected_ref = "rss-pautas" if action in QUEUE_ACTIONS else "binance-revisao-6e8da0b05713"
    if data["article_ref"] != expected_ref:
        raise ValueError("unsupported action reference")
    return jid, action


def invoke(argv, timeout=120):
    r = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout,
                       env={k: v for k, v in os.environ.items() if k not in {
                           "GROQ_API_KEY", "WP_USER", "WP_APP_PASSWORD", "CONEXO_WP_USER",
                           "CONEXO_WP_APP_PASSWORD", "TURSO_AUTH_TOKEN"
                       }})
    if r.returncode:
        return {"status": "FAILED", "exit_code": r.returncode,
                "output": (r.stdout + "\n" + r.stderr)[-3000:]}
    return {"status": "PASS", "exit_code": 0, "output": r.stdout[-3000:]}


def _atomic_receipt(path, info):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _previous_receipt(job_receipt, latest, jid):
    """Use per-job journal and migrate the last legacy receipt without replay."""
    if job_receipt.exists():
        return json.loads(job_receipt.read_text())
    if latest.is_file():
        legacy = json.loads(latest.read_text())
        if legacy.get("job_id") == jid:
            _atomic_receipt(job_receipt, legacy)
            return legacy
    return None


def main():
    # Keep legacy review path; queue bridge is additionally required only for queue actions.
    if not LAUNCHER.is_file() or LAUNCHER.is_symlink():
        raise SystemExit("BLOCKED: trusted local launcher missing")
    remote = subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT,
                            text=True, capture_output=True, timeout=10)
    if remote.returncode or remote.stdout.strip() not in {REPOSITORY, REPOSITORY.removesuffix(".git")}:
        raise SystemExit("BLOCKED: unexpected repository origin")
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(STATE, 0o700)
    os.umask(0o077)
    with (STATE / "remote-control.lock").open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("BLOCKED: another remote controller is running")
        fetched = subprocess.run(["git", "fetch", "--no-tags", "origin", "refs/heads/" + BRANCH],
                                 cwd=ROOT, capture_output=True, text=True, timeout=45)
        if fetched.returncode:
            raise SystemExit("BLOCKED: remote request fetch failed")
        requested = subprocess.run(["git", "show", "FETCH_HEAD:ops/hostinger/remote_request.json"],
                                   cwd=ROOT, capture_output=True, text=True, timeout=15)
        if requested.returncode:
            raise SystemExit("BLOCKED: remote request missing on trusted branch")
        try:
            jid, action = validate_request(json.loads(requested.stdout))
        except (ValueError, TypeError):
            raise SystemExit("BLOCKED: invalid or unauthorized remote request")
        if action in QUEUE_ACTIONS and (not QUEUE_BRIDGE.is_file() or QUEUE_BRIDGE.is_symlink()):
            raise SystemExit("BLOCKED: trusted queue bridge missing")
        # Durable per-ID receipts prevent replay when the GitHub request later
        # cycles back to a previously processed job ID. STARTED is non-retryable.
        jobs = STATE / "remote-jobs"
        jobs.mkdir(mode=0o700, exist_ok=True)
        os.chmod(jobs, 0o700)
        job_receipt = jobs / (jid + ".json")
        latest = STATE / "remote-control-receipt.json"
        previous = _previous_receipt(job_receipt, latest, jid)
        if previous is not None:
            print(json.dumps({"status": "ALREADY_PROCESSED", "job_id": jid,
                              "last_run_status": previous.get("status"),
                              "receipt": str(job_receipt)}))
            return
        entry = {"schema": "conexo-remote-receipt/1", "job_id": jid, "action": action,
                 "started_utc": datetime.now(timezone.utc).isoformat(),
                 "status": "STARTED", "wordpress_written": False,
                 "publication_authorized": False}
        _atomic_receipt(job_receipt, entry)
        _atomic_receipt(latest, entry)
        outcomes = []
        for flag in ALLOWED[action]:
            argv = ([sys.executable, str(QUEUE_BRIDGE), flag] if action in QUEUE_ACTIONS
                    else ["bash", str(LAUNCHER), flag])
            try:
                result = invoke(argv, timeout=120)
            except (OSError, subprocess.TimeoutExpired):
                result = {"status": "FAILED", "exit_code": -1, "output": "executor unavailable or timed out"}
            outcomes.append({"step": flag, **result})
            if result["status"] != "PASS":
                break
        entry.update(status="PASS" if len(outcomes) == len(ALLOWED[action]) and all(
            x["status"] == "PASS" for x in outcomes) else "FAILED",
            completed_utc=datetime.now(timezone.utc).isoformat(), results=outcomes)
        _atomic_receipt(job_receipt, entry)
        _atomic_receipt(latest, entry)
        print(json.dumps({"job_id": jid, "status": entry["status"],
                          "steps": len(outcomes), "receipt": str(job_receipt)}))


if __name__ == "__main__":
    main()
