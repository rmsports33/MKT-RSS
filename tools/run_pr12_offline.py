#!/usr/bin/env python3
"""Validação estrita offline do PR #12, sem alterar o checkout nem acionar serviços.

Preparação ONLINE (separada, em venv descartável):
    python -m pip install -r requirements/offline-validation.txt

Execução OFFLINE:
    python tools/run_pr12_offline.py --expected SHA_COMPLETO --output /tmp/pr12-evidencias
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile

REQUIRED = {
    "pytest": "pytest", "requests": "requests",
    "feedparser": "feedparser", "trafilatura": "trafilatura",
    "python-telegram-bot": "telegram",
}
SOURCES = (
    "mkt_flow_p0/price_api_clients.py",
    "mkt_flow_p0/price_collector.py",
    "mkt_flow_p0/comparativo_flow.py",
    "redator-artigo-blogs/src/generator/render.py",
    "tools/dry_run_preco_m0417f.py",
    "tools/pytest_offline_guard.py",
)
SENSITIVE_PREFIXES = (
    "WP_", "GROQ_", "OPENAI_", "TURSO_", "AMAZON_", "SHOPEE_",
    "MERCADOLIVRE_", "GOOGLE_", "TELEGRAM_", "FTP_", "SFTP_",
    "CLOUDFLARE_",
)


def execute(argv, cwd, env=None):
    return subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--expected", required=True, help="SHA de 40 caracteres visto no PR")
    ap.add_argument("--output", required=True, type=Path, help="pasta fora do checkout Git")
    args = ap.parse_args(argv)
    repo, out = args.repo.resolve(), args.output.resolve()
    if not re.fullmatch(r"[0-9a-f]{40}", args.expected.lower()):
        ap.error("SHA completo invalido")
    if out == repo or repo in out.parents or out in repo.parents:
        ap.error("output deve ficar fora da arvore do checkout")
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "BLOCKED", "expected": args.expected,
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "commands": [], "dependencies": {},
    }

    def done(status, reason=""):
        result.update(status=status, reason=reason)
        path = out / "resultado.json"
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        print(json.dumps({"status": status, "reason": reason, "report": str(path)},
                         ensure_ascii=False))
        return 0 if status == "PASS" else 2

    head = execute(["git", "rev-parse", "HEAD"], repo)
    if head.returncode:
        return done("BLOCKED_GIT", head.stderr[:300])
    result["head"] = head.stdout.strip()
    if result["head"] != args.expected.lower():
        return done("BLOCKED_HEAD", "checkout diferente do SHA indicado")
    dirty = execute(["git", "status", "--porcelain", "--untracked-files=no"], repo)
    if dirty.returncode or dirty.stdout.strip():
        return done("BLOCKED_CHECKOUT", "checkout nao limpo")

    missing = []
    for package, module in REQUIRED.items():
        try:
            if importlib.util.find_spec(module) is None:
                missing.append(package)
            else:
                result["dependencies"][package] = importlib.metadata.version(package)
        except (ValueError, importlib.metadata.PackageNotFoundError):
            missing.append(package)
    if missing:
        result["missing"] = missing
        return done("BLOCKED_DEPENDENCIES", "Instale requirements/offline-validation.txt antes de testar")

    archive = subprocess.run(["git", "archive", "--format=tar", "HEAD"],
                             cwd=repo, capture_output=True)
    if archive.returncode:
        return done("BLOCKED_ARCHIVE", archive.stderr.decode(errors="replace")[:300])
    env = os.environ.copy()
    for key in list(env):
        if key.startswith(SENSITIVE_PREFIXES):
            env.pop(key)
    env.update(COMPARATIVO_PUBLICACAO_ENABLED="false",
               GATE_PUBLICACAO_ENABLED="false",
               PYTHONDONTWRITEBYTECODE="1",
               PYTHONNOUSERSITE="1", PIP_NO_INDEX="1")

    with tempfile.TemporaryDirectory(prefix="pr12-isolado-") as tmp:
        work = Path(tmp)
        with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as tar:
            for member in tar.getmembers():
                resolved = (work / member.name).resolve()
                if not resolved.is_relative_to(work) or not (member.isfile() or member.isdir()):
                    return done("BLOCKED_ARCHIVE", "entrada insegura no archive")
            tar.extractall(work, filter="data")
        errors = []
        for path in SOURCES:
            try:
                ast.parse((work / path).read_text(encoding="utf-8"), filename=path)
            except Exception as e:
                errors.append({"path": path, "error": str(e)})
        if errors:
            result["syntax_errors"] = errors
            return done("FAIL_SYNTAX", "erro de sintaxe no HEAD")

        tasks = [
            ("focused", [sys.executable, "-m", "pytest", "-p", "tools.pytest_offline_guard",
                         "tests/unit/test_price_api_clients_p0.py",
                         "tests/unit/test_price_collector_p0.py", "-q", "-p", "no:cacheprovider"]),
            ("complete", [sys.executable, "-m", "pytest", "-p", "tools.pytest_offline_guard",
                          "tests", "redator-artigo-blogs/tests", "-q", "-rs",
                          "-p", "no:cacheprovider"]),
            ("dryrun", [sys.executable, "tools/dry_run_preco_m0417f.py"]),
        ]
        logs = {}
        for label, cmd in tasks:
            response = execute(cmd, work, env)
            output = response.stdout + ("\nSTDERR:\n" + response.stderr if response.stderr else "")
            path = out / (label + ".log")
            path.write_text(output, encoding="utf-8")
            logs[label] = response.stdout
            result["commands"].append({
                "name": label, "command": cmd, "exit": response.returncode,
                "log": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
        try:
            proof = json.loads(logs["dryrun"])
        except (ValueError, TypeError):
            proof = {}
        receipt = proof.get("resultado") or {}
        dry_ok = (
            proof.get("tipo") == "fixture_sintetica_sem_cotacao_real"
            and proof.get("http_real") == 0
            and proof.get("sqlite_escritas") == 0
            and proof.get("respostas_simuladas") == 2
            and receipt.get("acao") == "dry_run_ok"
            and receipt.get("escreveu") is False
            and receipt.get("publicacao_ativa") is False
        )
        network_ok = all("OFFLINE GUARD: conexoes permitidas=0" in logs[k]
                         for k in ("focused", "complete"))
        result["gates"] = {"dry_run": dry_ok, "network": network_ok}
        result["test_summary"] = [
            x.strip() for x in logs["complete"].splitlines()
            if re.search(r"\b\d+ (passed|failed|skipped|deselected)\b", x)
        ]
        if all(entry["exit"] == 0 for entry in result["commands"]) and dry_ok and network_ok:
            return done("PASS")
        return done("FAIL", "veja logs; nao autorizar homologacao real")


if __name__ == "__main__":
    sys.exit(main())
