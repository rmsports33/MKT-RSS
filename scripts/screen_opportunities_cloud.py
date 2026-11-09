"""Workflow bridge: repository input only, counters only in public summary."""
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mkt_flow_p0.opportunities import evaluate, load_candidates


def main():
    path = (ROOT / os.environ.get("INPUT_FILE", "")).resolve()
    if not path.is_relative_to(ROOT) or path.suffix not in {".csv", ".json"}:
        raise ValueError("input must be a JSON/CSV within checkout")
    items = [evaluate(i) for i in load_candidates(path)]
    summary = {"schema": "conexo-opportunity-summary/1", "counts": dict(Counter(i["status"] for i in items)),
               "publication_authorized": False, "private_content_exported": False}
    rendered = json.dumps(summary, ensure_ascii=False)
    print(rendered)
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(rendered + "\n")


if __name__ == "__main__":
    main()
