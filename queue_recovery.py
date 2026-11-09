"""Explicit offline export/restore for a private SQLite queue."""
import argparse
import json
from mkt_flow_p0.queue_snapshot import export_queue, restore_queue


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("export", "restore"))
    p.add_argument("source")
    p.add_argument("target")
    p.add_argument("--manifest")
    args = p.parse_args()
    try:
        if args.action == "restore" and not args.manifest:
            p.error("restore exige --manifest")
        out = (export_queue(args.source, args.target) if args.action == "export"
               else restore_queue(args.source, args.target, args.manifest))
        print(json.dumps(out, ensure_ascii=False))
        return 0
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "BLOQUEADO", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
