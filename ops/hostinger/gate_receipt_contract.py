#!/usr/bin/env python3
"""Offline, read-only inventory of installed Conexo Gate receipt/signature contract.

Do not send source code, secrets, request bodies, or authentication tokens to
stdout. Only structural, allowlisted markers leave this process. NO HTTP.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ops.hostinger.gate_stage_preflight import detect_file
from ops.hostinger.gate_stage_contract import extract_function

IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
FIELDS = re.compile(
    r"\$(?:request|receipt|payload|data|body|claims|review|meta|params|envelope|signed|input|snapshot|decoded)"
    r"\s*\[\s*['\"]([A-Za-z][A-Za-z0-9_-]{0,63})['\"]\s*\]")
METHOD_FIELDS = re.compile(
    r"->\s*get_param\s*\(\s*['\"]([A-Za-z][A-Za-z0-9_-]{0,63})['\"]\s*\)")
CALLS = re.compile(r"\b(cxeg_[A-Za-z0-9_]+)\s*\(")
KEYWORD = ("receipt", "signature", "stage", "draft", "publish", "schedule",
           "hash_equals", "hash_hmac", "hmac", "sha256", "base64_decode",
           "wp_insert_post", "wp_update_post", "get_param", "get_json_params",
           "json_decode", "json_encode", "current_user_can", "version_sha256",
           "content_sha256", "nonce", "idempotency", "featured_media",
           "post_status", "post_title", "post_content", "wp_error")
SEED_FUNCS = ("cxeg_write", "cxeg_write_locked", "cxeg_decode", "cxeg_hash",
              "cxeg_snapshot", "cxeg_permission")
SENSITIVE = re.compile(r"password|secret|token|authorization|credential|private|api.key", re.I)


def examine(source, name):
    body = extract_function(source, name)
    if body is None:
        return {"present": False}
    field_names = sorted(set(FIELDS.findall(body)) | set(METHOD_FIELDS.findall(body)))
    field_names = [x for x in field_names if IDENT.fullmatch(x) and not SENSITIVE.search(x)]
    calls = sorted(set(CALLS.findall(body)) - {name})
    controls = [x for x in KEYWORD if re.search(r"\b" + re.escape(x) + r"\b", body, re.I)]
    # Only show literal possible action values/route methods, no source values
    # other than allowlisted field names and names of own local functions.
    array_inputs = sorted(set(
        re.findall(r"\$(?:request|receipt|payload|data|body)\s*(?:->\s*get_[a-z_]+\s*\(\s*)?"
                   r"['\"]([A-Za-z][A-Za-z0-9_-]{0,63})['\"]", body)
    ))
    return {
        "present": True,
        "lines": len(body.splitlines()),
        "fields_seen": field_names,
        "local_calls": calls[:50],
        "control_tokens": controls,
        "request_accessors": sorted(set(re.findall(
            r"->\s*(get_param|get_json_params|get_body_params|get_params)\s*\(", body
        ))),
        "gate_error_codes": sorted(set(re.findall(
            r"['\"](cxeg_[a-z0-9_-]{3,64})['\"]", body, re.I
        )))[:30],
        "literal_intents_seen": [value for value in ("stage", "publish", "schedule")
                                 if re.search(r"['\"]" + value + r"['\"]", body)],
    }


def analyze(source):
    # Follow at most 20 locally declared functions. Include signature and
    # receipt helpers but never dump raw PHP statements to the terminal.
    names = list(SEED_FUNCS)
    result = {}
    while names and len(result) < 20:
        name = names.pop(0)
        if name in result:
            continue
        detail = examine(source, name)
        result[name] = detail
        if detail["present"]:
            for called in detail["local_calls"]:
                if called not in result and called not in names:
                    names.append(called)
    return result


def main():
    path, error = detect_file()
    if error:
        print(json.dumps({"status": "BLOCKED", "reason": error, "wp_write": False}))
        return 2
    source = path.read_text(encoding="utf-8", errors="replace")
    functions = analyze(source)
    print(json.dumps({
        "status": "GATE_RECEIPT_CONTRACT_READ_ONLY",
        "source": "installed_gate_php",
        "functions": functions,
        "stage_executor_ready": False,
        "wp_write": False,
        "publication_authorized": False,
        "next": "Interpret structural contract and implement stage-only client with an authenticated, existing, least-privileged credential. Signature MUST be produced and verified by the trusted Gate mechanism.",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
