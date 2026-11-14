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
    """Return function body by balancing PHP braces, not by the next function.

    This is a bounded structural scanner; comments/strings with curly braces
    could affect matching, so its output is diagnostic, not an API contract.
    """
    m = re.search(r"\bfunction\s+" + re.escape(name) + r"\s*\(", source)
    if not m:
        return None
    open_brace = source.find("{", m.end())
    if open_brace < 0 or open_brace - m.end() > 2000:
        return None
    depth = 0
    for i in range(open_brace, min(len(source), open_brace + 60000)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return source[m.start():i + 1]
    return None


def structural_info(source, root_name):
    # Follow direct cxeg_* function calls, at most three levels and six funcs.
    # Never execute PHP or expose free-form source text.
    queue = [(root_name, 0)]
    visited = set()
    keys, funcs, controls, param_methods = set(), [], set(), set()
    while queue and len(visited) < 6:
        name, depth = queue.pop(0)
        if name in visited:
            continue
        visited.add(name)
        body = extract_function(source, name)
        if body is None:
            continue
        funcs.append(name)
        patterns = (
            r"\$(?:request|params|payload|data|args)\s*\[\s*['\"]([\w-]{1,65})['\"]\s*\]",
            r"\$(?:request|req)\s*->\s*get_param\s*\(\s*['\"]([\w-]{1,65})['\"]",
            r"\$(?:request|req)\s*->\s*get_(?:string|int|bool)_param\s*\(\s*['\"]([\w-]{1,65})['\"]",
        )
        for pattern in patterns:
            keys.update(v for v in re.findall(pattern, body)
                        if IDENT.fullmatch(v) and not SENSITIVE.search(v))
        for word in ("stage", "publish", "schedule", "draft", "wp_insert_post",
                     "wp_update_post", "current_user_can", "wp_verify_nonce",
                     "hash_equals", "review", "signature", "featured_media",
                     "post_id", "version_sha256", "content_sha256", "idempotency"):
            if re.search(r"\b" + re.escape(word) + r"\b", body, re.I):
                controls.add(word)
        for method in ("get_json_params", "get_body_params", "get_params", "get_param"):
            if "->" + method + "(" in body or re.search(r"->\s*" + method + r"\s*\(", body):
                param_methods.add(method)
        if depth < 3:
            for child in re.findall(r"\b(cxeg_[A-Za-z0-9_]+)\s*\(", body):
                if child not in visited and child != name and len(queue) < 12:
                    queue.append((child, depth + 1))
    return {
        "found": bool(funcs),
        "functions_followed": funcs,
        "parameter_keys_seen": sorted(keys),
        "request_accessors_seen": sorted(param_methods),
        "control_keywords_seen": sorted(controls),
        "diagnostic_only": True,
    }


def safe_contract(source):
    return {name: structural_info(source, name) for name in FUNCTIONS}


def _fetch_index(url, max_bytes=4000000):
    request = Request(url, headers={
        "User-Agent": "Conexo-Gate-Stage-Preflight/3",
        "Accept": "application/json",
        "Accept-Encoding": "identity",
    })
    with urlopen(request, timeout=18) as response:
        data = response.read(max_bytes + 1)
        return data[:max_bytes], len(data) > max_bytes, response.status, (
            response.headers.get("Content-Type", "").split(";")[0].strip().lower())


def index_probe():
    # Namespace endpoint is much smaller than the global WordPress REST index.
    # GET and OPTIONS are read-only; NEVER POST.
    results = []
    for url in (
        "https://" + DOMAIN + "/wp-json/conexo/v1",
        "https://" + DOMAIN + "/?rest_route=/conexo/v1",
        "https://" + DOMAIN + "/wp-json/",
    ):
        try:
            data, truncated, code, mime = _fetch_index(url)
            result = {"path":url.split(DOMAIN, 1)[-1],
                      "http_status":code, "content_type":mime,
                      "bytes_received":len(data), "truncated":truncated}
            if truncated:
                result["json_valid"] = False
                result["diagnostic"] = "response_truncated"
            else:
                try:
                    root = json.loads(data)
                    result["json_valid"] = True
                    routes = root.get("routes", {}) if isinstance(root, dict) else {}
                    match = routes.get("/conexo/v1/editorial/write")
                    result["route_visible"] = isinstance(match, dict)
                    if isinstance(match, dict):
                        result["methods"] = [x.get("methods") for x in match.get("endpoints", [])]
                        result["public_args"] = sorted({
                            k for x in match.get("endpoints", [])
                            for k in x.get("args", {}) if IDENT.fullmatch(k) and not SENSITIVE.search(k)
                        })
                except (ValueError, TypeError, UnicodeDecodeError) as exc:
                    result["json_valid"] = False
                    result["parse_error"] = type(exc).__name__
                    result["looks_like_html"] = data.lstrip().startswith((b"<!doctype", b"<html", b"<"))
            results.append(result)
            if result.get("route_visible"):
                break
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            results.append({"path":url.split(DOMAIN, 1)[-1],
                            "http_status":getattr(exc, "code", None),
                            "error_type":type(exc).__name__})
    return results


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
