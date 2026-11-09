"""Cloud/manual CLI: JSON/CSV -> review queue report. Standard library only."""
import argparse
import json
from pathlib import Path
from mkt_flow_p0.opportunities import evaluate, load_candidates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--now", help="ISO timestamp com timezone, para replay")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = {"schema": "conexo-opportunity-batch/1", "mode": "offline_no_ai_no_wordpress",
                  "items": [evaluate(i, now=args.now) for i in load_candidates(args.input)]}
        rendered = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.output:
            # Never overwrite an existing evidence file.
            with args.output.open("x", encoding="utf-8") as f:
                f.write(rendered)
        else:
            print(rendered, end="")
        return 0
    except (ValueError, TypeError, KeyError, OSError) as ex:
        print(json.dumps({"status": "BLOQUEADO", "error": str(ex)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
