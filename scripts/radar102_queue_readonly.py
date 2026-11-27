"""Read-only, paginated candidate matching against the EXISTING daily Turso queue.

Run only inside the existing authorized daily GitHub Actions secrets scope.
Never prints article bodies, private queue titles, URLs or credentials.
"""
import json
import re
from mkt_flow_p0.live_queue_demand import connection_context, readonly_execute

CANDIDATES = {
    "motorola-signature-27": (r"\\bmotorola\\s+signature\\s*27\\b",),
    "galaxy-s26-fe": (r"\\bgalaxy\\s+s26\\s*fe\\b",),
    "hisense-qd6sf": (r"\\bhisense\\s+qd6sf\\b",),
    "tcl-c6k": (r"\\btcl\\s+c6k\\b",),
    "galaxy-book4": (r"\\bgalaxy\\s+book\\s*4\\b",),
    "moto-buds-2-ultra": (r"\\bmoto\\s+buds\\s*2\\s*ultra\\b",),
    "amazfit-bip-6": (r"\\bamazfit\\s+bip\\s*6\\b",),
    "viewfinity-s7": (r"\\bviewfinity\\s+s7\\b",),
    "galaxy-tab-s10-fe": (r"\\bgalaxy\\s+tab\\s+s10\\s*fe\\b",),
    "ps5-slim-digital": (r"\\b(?:ps5|playstation\\s*5)\\s+slim\\s+digital\\b",),
}
PAGE_SIZE = 200
MAX_PAGES = 100


def scan(execute=readonly_execute):
    connection_context()  # no local SQLite fallback
    check = execute("SELECT name FROM sqlite_master WHERE type=? AND name=?", ("table", "rss_pautas"))
    if check.get("rows") != [["rss_pautas"]]:
        raise ValueError("DAILY_QUEUE_TABLE_NOT_FOUND")
    hits = {key: {"count": 0, "states": {}} for key in CANDIDATES}
    count = 0
    complete = False
    for page in range(MAX_PAGES):
        response = execute(
            "SELECT titulo,estado FROM rss_pautas ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (PAGE_SIZE, page * PAGE_SIZE),
        )
        if not isinstance(response, dict) or "erro" in response or not isinstance(response.get("rows"), list):
            raise ValueError("DAILY_QUEUE_READ_FAILED")
        rows = response["rows"]
        for row in rows:
            if not isinstance(row, list) or len(row) != 2 or not isinstance(row[0], str):
                raise ValueError("DAILY_QUEUE_INVALID_ROW")
            count += 1
            for key, patterns in CANDIDATES.items():
                if any(re.search(pattern, row[0], re.I) for pattern in patterns):
                    hits[key]["count"] += 1
                    state = str(row[1])
                    hits[key]["states"][state] = hits[key]["states"].get(state, 0) + 1
        if len(rows) < PAGE_SIZE:
            complete = True
            break
    return {"schema": "radar102-queue-dedupe/1", "read_only": True,
            "complete_scan": complete, "rows_examined": count,
            "candidate_matches": hits, "publication_authorized": False,
            "caution": "Exact title matches only; zero hits does not exclude semantic duplicates."}


if __name__ == "__main__":
    try:
        print(json.dumps(scan(), sort_keys=True))
    except Exception as exc:
        reason = str(exc) if isinstance(exc, ValueError) and re.fullmatch("[A-Z0-9_]+", str(exc)) else type(exc).__name__
        print(json.dumps({"status": "BLOCKED", "reason": reason}))
        raise SystemExit(1)
