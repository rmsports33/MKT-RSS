#!/usr/bin/env python3
"""Find the EXISTING trusted Gate receipt issuer without using credentials.

Runs read-only on Hostinger. Does not reproduce HMAC secrets or signatures.
Scans installed Gate PHP (not the GitHub branch) and prints just the structural
locations of signing, verification, routes and human-review controls.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ops.hostinger.gate_stage_preflight import detect_file
from ops.hostinger.gate_stage_contract import extract_function

FUN = re.compile(r"\bfunction\s+([A-Za-z_]\w*)\s*\(")
REST = re.compile(r"register_rest_route\s*\(\s*['\"]([^'\"]{1,80})['\"]\s*,\s*['\"]([^'\"]{1,120})['\"]", re.S)
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,79}$")
SECRETS = re.compile(r"secret|token|pass|key|credential|auth|private|salt", re.I)
MARKERS = ("hash_hmac", "hash_equals", "base64_encode", "base64_decode",
           "wp_json_encode", "json_encode", "wp_insert_post",
           "current_user_can", "wp_verify_nonce", "wp_create_nonce",
           "cxeg_review_identity_valid", "cxeg_quality_valid")
FIELDS = re.compile(r"\$(?:receipt|request|payload|data|body|claims|params|review|meta|envelope|snapshot)\s*\[\s*['\"]([a-zA-Z][a-zA-Z0-9_-]{0,64})['\"]")
TARGET = "conexo-editorial-gate"


def issuer_candidates(root):
    php_paths = sorted(root.rglob("*.php"))
    if len(php_paths) > 35:
        raise ValueError("unexpected_number_of_plugin_files")
    result = []
    for path in php_paths:
        if path.is_symlink() or path.stat().st_size > 200_000:
            raise ValueError("unsafe_plugin_file")
        body = path.read_text(encoding="utf-8", errors="replace")
        findings = []
        for m in FUN.finditer(body):
            name = m.group(1)
            if not IDENT.fullmatch(name):
                continue
            block = extract_function(body, name)
            if not block:
                continue
            markers = [marker for marker in MARKERS if marker in block]
            related = any(term in name.lower() for term in (
                "receipt", "sign", "review", "approve", "write", "stage",
                "broker", "hmac", "quality", "publish"))
            if not related and not ("hash_hmac" in markers or "base64_encode" in markers):
                continue
            fields = sorted(set(x for x in FIELDS.findall(block) if not SECRETS.search(x)))
            findings.append({
                "function":name,
                "markers":markers,
                "fields":fields[:24],
                "is_hmac_candidate": "hash_hmac" in markers,
                "may_emit_receipt": "hash_hmac" in markers and (
                    "base64_encode" in markers or "json_encode" in markers or "wp_json_encode" in markers),
            })
        routes = sorted(set(a.strip("/") + "/" + b.strip("/") for a,b in REST.findall(body)))
        if findings or routes:
            result.append({
                "file":path.relative_to(root).as_posix(),
                "functions":findings[:50],
                "routes":routes[:35],
            })
    return result


def main():
    path, error = detect_file()
    if error:
        print(json.dumps({"status":"BLOCKED","reason":error,"wordpress_written":False}))
        return 2
    root = path.parent.parent
    if root.name != TARGET or root.is_symlink():
        print(json.dumps({"status":"BLOCKED","reason":"wrong_plugin_root","wordpress_written":False}))
        return 2
    try:
        findings = issuer_candidates(root)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status":"BLOCKED","reason":type(exc).__name__,"wordpress_written":False}))
        return 2
    candidates = [
        {"file":item["file"],"function":f["function"]}
        for item in findings for f in item["functions"] if f["may_emit_receipt"]
    ]
    print(json.dumps({
        "status":"ISSUER_DISCOVERY_READ_ONLY",
        "plugin_root_validated":True,
        "possible_receipt_issuers":candidates,
        "inventory":findings,
        "actual_receipt_issued":False,
        "factual_approval":False,
        "wordpress_written":False,
        "publication_authorized":False,
        "notice":"Candidate does not imply authorisation; identify trusted reviewer flow and schema before stage."
    }, ensure_ascii=False, indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
