#!/usr/bin/env python3
"""Read-only Gate route contract extraction from installed local PHP; no HTTP writes.

Extract only structural parameter and gate condition signatures without
displaying PHP source values or secrets. No need for WordPress credentials.
"""
import json
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ops.hostinger.gate_stage_preflight import detect_file, DOMAIN

FUNCTIONS = ("cxeg_write", "cxeg_permission")
# Parameter names and literal string keys are the only admitted source-derived
# data. These are limited to identifiers, never arbitrary PHP values.
IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,64}$")
SENSITIVE = re.compile(r"password|secret|token|authorization|private|key|credential", re.I)


def extract_function(source, name):
    m = re.search(r"\bfunction\s+" + re.escape(name) + r"\s*\(", source)
    if not m:
        return None
    # Extract until the next top-level function declaration. This is a
    # diagnostic approximation, not a PHP parser or an execution contract.
    following = re.search(r"\bfunction\s+[A-Za-z_]\w*\s*\(", source[m.end():])
    end = m.end() + following.start() if following else len(source)
    return source[m.start():min(end, m.start() + 14000)]


def safe_contract(source):
    extracted = {}
    for function in FUNCTIONS:
        body = extract_function(source, function)
        if body is None:
            extracted[function] = {"found": False}
            continue
        candidates = set()
        patterns = (
            r"\$request\s*\[\s*['\"]([\w-]{1,65})['\"]\s*\]",
            r"\$request\s*->\s*get_param\s*\(\s*['\"]([\w-]{1,65})['\"]",
            r"\$request\s*->\s*get_(?:string|int|bool)_param\s*\(\s*['\"]([\w-]{1,65})['\"]",
            r"(?:isset|empty)\s*\(\s*\$request\s*\[\s*['\"]([\w-]{1,65})['\"]",
        )
        for pattern in patterns:
            for match in re.findall(pattern, body):
                if IDENT.fullmatch(match) and not SENSITIVE.search(match):
                    candidates.add(match)
        # Whitelist booleans rather than printing raw source code. A hit means
        # "seen in source", NOT a validated endpoint payload requirement.
        keywords = ("stage", "publish", "schedule", "draft", "status",
                    "wp_insert_post", "wp_update_post", "current_user_can",
                    "wp_verify_nonce", "hash_equals", "permission",
                    "review", "signature", "featured_media", "post_id",
                    "version_sha256", "content_sha256", "idempotency")
        observed = [keyword for keyword in keywords if re.search(r"\b" + re.escape(keyword) + r"\b", body, re.I)]
        extracted[function] = {
            "found": True, "parameter_keys_seen": sorted(candidates),
            "control_keywords_seen": observed,
            "lines_approx": len(body.splitlines()),
        }
    return extracted


def index_probe():
    request = Request("https://" + DOMAIN + "/wp-json/", headers={"User-Agent":"Conexo-Gate-Stage-Preflight/2","Accept":"application/json"})
    try:
        with urlopen(request, timeout=12) as response:
            data = response.read(500000)
            mime = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
            code = response.status
        result = {"http_status":code,"content_type":mime}
        try:
            root = json.loads(data)
            routes = root.get("routes", {}) if isinstance(root, dict) else {}
            result["json_valid"] = True
            match = routes.get("/conexo/v1/editorial/write")
            if isinstance(match, dict):
                result["route_visible"] = True
                result["methods"] = [x.get("methods") for x in match.get("endpoints", [])]
                result["public_args"] = sorted(set(k for x in match.get("endpoints", []) for k in x.get("args", {}) if IDENT.fullmatch(k) and not SENSITIVE.search(k)))
            else:
                result["route_visible"] = False
        except (ValueError, TypeError):
            result["json_valid"] = False
            # Only classify the response's first byte, never echo potentially
            # confidential response HTML or full headers.
            result["looks_like_html"] = data.lstrip().startswith((b"<!doctype", b"<html", b"<"))
        return result
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return {"http_status":getattr(exc, "code", None), "error_type":type(exc).__name__}


def main():
    file, error = detect_file()
    if error:
        print(json.dumps({"status":"BLOCKED","stage_writes":False, **error}))
        return 2
    source = file.read_text(encoding="utf-8", errors="replace")
    print(json.dumps({
        "status":"READ_ONLY_CONTRACT_PROBE",
        "installed_php_functions": safe_contract(source),
        "rest_index":index_probe(),
        "no_stage_writes":True, "publication_authorized":False,
        "warning":"Source key occurrences are NOT a validated request schema or permission to stage."
    }, ensure_ascii=False, indent=2))
    return 0


if __name__=="__main__":
    sys.exit(main())
