"""Private file import/replay without AI, network or database dependencies."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from mkt_flow_p0.demand_evidence import build, save_file, load_file, replay, MAX_BYTES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('pack', 'replay'))
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--pauta-id', required=True)
    parser.add_argument('--pauta-url', required=True)
    parser.add_argument('--query')
    parser.add_argument('--at')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--reviewer')
    parser.add_argument('--review-reason')
    parser.add_argument('--reviewed-at')
    args = parser.parse_args()
    now = args.at or datetime.now(timezone.utc).isoformat()
    if args.mode == 'pack':
        if not args.output or not args.query:
            parser.error('pack requires --output and --query')
        with args.input.open('rb') as stream:
            data = stream.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError('INPUT_TOO_LARGE')
        fields = (args.reviewer, args.review_reason, args.reviewed_at)
        if any(fields) and not all(fields):
            parser.error('review requires reviewer, reason and reviewed-at')
        review = dict(zip(('reviewer', 'reason', 'reviewed_at'), fields)) if all(fields) else None
        bundle = build(args.pauta_id, args.pauta_url, json.loads(data), args.query, now=now, review=review)
        result = save_file(bundle, args.output)
        result['query_review_status'] = bundle['payload']['query_review']['status']
    else:
        result = replay(load_file(args.input), pauta_id=args.pauta_id, pauta_url=args.pauta_url, now=now)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
