"""One bounded research request; optional adapter, no AI or WordPress."""
import argparse
import json
from pathlib import Path
from mkt_flow_p0 import research_signals


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("provider", choices=("autocomplete", "trends"))
    p.add_argument("terms", nargs="+")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if args.provider == "autocomplete" and len(args.terms) != 1:
        p.error("autocomplete recebe uma semente por chamada")
    result = (research_signals.autocomplete(args.terms[0]) if args.provider == "autocomplete"
              else research_signals.trends(args.terms))
    value = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        with args.output.open("x", encoding="utf-8") as f:
            f.write(value + "\n")
    else:
        print(value)
    return 0 if result["status"] in {"SUGESTOES_OBSERVADAS", "SNAPSHOT_NAO_VALIDADO"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
