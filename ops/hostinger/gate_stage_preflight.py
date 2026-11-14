#!/usr/bin/env python3
"""Read-only preflight of the installed Conexo Editorial Gate stage contract.

Reads local PHP route registration and checks public REST route discovery.
NO POST, credentials, WordPress writes or publication. Prints bounded excerpts
and rejects missing or ambiguous plugin installations.
"""
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DOMAIN = "conexotech.com.br"
TARGET = "conexo/v1/editorial/write"
REL = "wp-content/plugins/conexo-editorial-gate/includes/conexo-editorial-gate-core.php"
ROOT = Path.home()
MAX_FILE = 200000


def detect_file():
    roots = [
        ROOT / "domains" / DOMAIN / "public_html",
        ROOT / "public_html",
    ]
    matches = [p / REL for p in roots if (p / REL).is_file() and not (p / REL).is_symlink()]
    if len(matches) != 1:
        return None, {"code": "GATE_FILE_MISSING_OR_AMBIGUOUS", "candidates_found": len(matches)}
    path = matches[0]
    if path.stat().st_size > MAX_FILE:
        return None, {"code": "GATE_FILE_TOO_LARGE"}
    return path, None


def local_route_excerpt(body):
    # Check route presence without treating content strings as executable.
    occurrences = [m.start() for m in re.finditer(r"editorial/write|editorial['\"]\s*,\s*['\"]/write", body)]
    if not occurrences:
        return {"status": "NOT_IDENTIFIED", "route_mentions": 0, "snippets": []}
    snippets = []
    for pos in occurrences[:6]:
        before = max(0, pos - 600)
        after = min(len(body), pos + 850)
        snippet = body[before:after]
        # Prevent leaking credential strings accidentally embedded in PHP:
        # only show lines containing structural route/callback/permission hints.
        hints = []
        for line in snippet.splitlines():
            if re.search(r"register_rest_route|editorial/write|permission_callback|callback|WP_REST|intent|stage|publish|schedule|args|nonce|current_user_can", line, re.I):
                if re.search(r"password|secret|token|authorization|api[_-]?key", line, re.I):
                    continue
                hints.append(line.strip()[:180])
        snippets.append(hints[:15])
    return {"status": "FOUND_IN_PHP", "route_mentions": len(occurrences), "snippets": snippets}


def public_rest_probe():
    # Route discovery only. OPTIONS and GET on public REST index never stage posts.
    url = "https://" + DOMAIN + "/wp-json/"
    req = Request(url, headers={"User-Agent": "Conexo-Gate-Stage-Preflight/1"})
    try:
        with urlopen(req, timeout=12) as response:
            data = response.read(500000)
            root = json.loads(data)
        routes = root.get("routes", {})
        matches = [r for r in routes if r.strip("/") == "/" + TARGET or r.strip("/") == TARGET]
        descriptions = {}
        for name in matches:
            info = routes[name]
            endpoints = info.get("endpoints", [])
            descriptions[name] = [{"methods": e.get("methods"), "args": sorted(e.get("args", {}).keys())} for e in endpoints]
        return {"status": "REST_INDEX_OK", "route_present": bool(matches), "descriptions": descriptions}
    except (HTTPError, URLError, ValueError, TimeoutError, OSError) as e:
        return {"status": "REST_INDEX_UNAVAILABLE", "error_type": type(e).__name__}


def main():
    path, error = detect_file()
    if error:
        print(json.dumps({"status": "BLOCKED", "stage_writes": False, **error}, ensure_ascii=False))
        return 2
    body = path.read_text(encoding="utf-8", errors="replace")
    local = local_route_excerpt(body)
    remote = public_rest_probe()
    print(json.dumps({
        "status": "READ_ONLY_PREFLIGHT",
        "gate_file_present": True,
        "local": local,
        "rest": remote,
        "stage_writes": False,
        "publication_authorized": False,
        "note": "No credential collection. Route field contract must be reviewed before any stage implementation."
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
