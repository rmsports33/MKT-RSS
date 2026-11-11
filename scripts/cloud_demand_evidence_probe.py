"""Private real series retention in existing homolog. Public hashes only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mkt_flow_p0.demand_evidence import build, replay, save_file
from mkt_flow_p0 import demand_evidence_turso as store

HOST = 'mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io'


def guard():
    if (os.getenv('TURSO_DATABASE_URL') != 'libsql://' + HOST
            or os.getenv('CONEXO_DEMAND_TURSO_ALLOWED_HOST') != HOST or not store.configured()):
        raise ValueError('HOMOLOG_NOT_CONFIGURED')


def write():
    from scripts.cloud_editorial_probe import rss_shadow
    from mkt_flow_p0.research_signals import trends
    from mkt_flow_p0.fila_pautas import _url
    rss_shadow()
    candidate = json.loads(Path('shadow-real.json').read_text(encoding='utf-8'))['input'][0]
    query = candidate['title']
    response = trends([query])
    if response['status'] != 'SNAPSHOT_NAO_VALIDADO':
        raise ValueError('TRENDS_' + response['status'])
    url = _url(candidate['url'])
    # Canonical queue identity, WITHOUT inserting/registering or claiming row exists.
    pauta_id = hashlib.sha256(url.encode()).hexdigest()[:32]
    bundle = build(pauta_id, url, response['raw'], query, now=datetime.now(timezone.utc))
    save_file(bundle, 'demand-evidence-private.json')
    result = store.save(bundle)
    if not result.get('ok'):
        raise ValueError(result['reason'])
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as stream:
            stream.write('digest=' + bundle['sha256'] + '\n')
            stream.write('pauta_id=' + pauta_id + '\n')
            stream.write('url_digest=' + hashlib.sha256(url.encode()).hexdigest() + '\n')
    return {'mode': 'write', 'sha256': bundle['sha256'], 'exact_readback': True,
            'query_review_status': 'PENDING', 'queue_row_verified': False}


def read():
    result = store.get(os.getenv('EVIDENCE_DIGEST', ''))
    if not result.get('ok'):
        raise ValueError(result['reason'])
    bundle = result['bundle']; payload = bundle['payload']
    if (payload['pauta_id'] != os.getenv('EXPECTED_PAUTA_ID') or
            hashlib.sha256(payload['pauta_url'].encode()).hexdigest() != os.getenv('EXPECTED_URL_DIGEST')):
        raise ValueError('PAUTA_ASSOCIATION_MISMATCH')
    result = replay(bundle, pauta_id=payload['pauta_id'], pauta_url=payload['pauta_url'])
    return {'mode': 'recover', 'sha256': bundle['sha256'], 'exact_replay': result['exact_replay'],
            'series_points': len(payload['source']['interest_over_time']),
            'query_review_status': result['query_review_status'], 'queue_row_verified': False}


def bind():
    from mkt_flow_p0.demand_queue_binding import check_binding
    result = store.get(os.getenv('EVIDENCE_DIGEST', ''))
    if not result.get('ok'):
        raise ValueError(result['reason'])
    return dict(check_binding(result['bundle']), scope='existing-homolog-only')


def main():
    parser = argparse.ArgumentParser();parser.add_argument('mode', choices=('write', 'read', 'bind'))
    args = parser.parse_args()
    try:
        guard()
        result = bind() if args.mode == 'bind' else (write() if args.mode == 'write' else read())
        result.update(publication_authorized=False, queue_changed=False)
        print(json.dumps(result, sort_keys=True))
        return 2 if result.get('status') == 'BLOCKED' else 0
    except Exception as exc:
        # Never log remote messages, article titles, queries, series or secrets.
        reason = str(exc) if isinstance(exc, ValueError) and re.fullmatch('[A-Z0-9_]+', str(exc)) else type(exc).__name__
        print(json.dumps({'status': 'BLOCKED', 'reason': reason}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
