"""Read actual queue, then retain demand in existing homolog in a separate job."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mkt_flow_p0.live_queue_demand import choose_existing


def select():
    candidate = choose_existing()
    if candidate.get('status') == 'BLOCKED':
        return candidate
    # Reference to an already-published source + literal entity only. Never a
    # private draft/title/body, credential, raw database or article claim.
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as stream:
            stream.write('candidate=' + json.dumps(candidate, separators=(',', ':'), ensure_ascii=True) + '\n')
    return {'mode': 'select', 'queue_reference_verified': True,
            'pauta_id': candidate['pauta_id'], 'query': candidate['query'],
            'source_url': candidate['pauta_url'], 'published_at': candidate['published_at'],
            'query_origin': candidate['query_origin'], 'human_query_review': 'PENDING',
            'connection': candidate['connection'], 'queue_changed': False}


def measure():
    from scripts.cloud_demand_evidence_probe import guard, HOST
    from mkt_flow_p0.research_signals import trends
    from mkt_flow_p0.demand_evidence import build
    from mkt_flow_p0 import demand_evidence_turso as storage
    guard()  # Strict existing HOMOLOG host; never writes the daily database.
    candidate = json.loads(os.environ['CANDIDATE_JSON'])
    # Outputs are passed only from this same trusted workflow, not Issue input.
    if (candidate.get('schema') != 'conexo-live-queue-research-candidate/1'
            or candidate.get('queue_reference_verified') is not True
            or candidate.get('queue_changed') is not False):
        raise ValueError('INVALID_QUEUE_REFERENCE')
    from mkt_flow_p0.opportunities import recent
    now = datetime.now(timezone.utc)
    if (not recent(candidate.get('queue_checked_at'), now, 1)
            or not recent(candidate.get('published_at'), now, 168)):
        raise ValueError('QUEUE_REFERENCE_EXPIRED')
    if candidate['connection']['host_sha256'] == hashlib.sha256(HOST.encode()).hexdigest():
        raise ValueError('EVIDENCE_TARGET_EQUALS_DAILY_DATABASE')
    query = candidate['query']
    source_context = None
    if candidate.get('topic_proposal'):
        from mkt_flow_p0.public_source_context import verify_context
        source_context = verify_context(candidate['pauta_url'], candidate['topic_proposal']['required_source_terms'])
    response = trends([query])
    if response['status'] != 'SNAPSHOT_NAO_VALIDADO':
        raise ValueError('TRENDS_' + response['status'])
    bundle = build(candidate['pauta_id'], candidate['pauta_url'], response['raw'], query,
                   now=datetime.now(timezone.utc))
    saved = storage.save(bundle)
    if not saved.get('ok'):
        raise ValueError(saved['reason'])
    # Confirm same private record after persistence, including full original series.
    result = storage.get(bundle['sha256'])
    if not result.get('ok') or result['bundle'] != bundle:
        raise ValueError('DEMAND_READBACK_FAILED')
    return {'mode': 'measure', 'sha256': bundle['sha256'], 'pauta_id': candidate['pauta_id'],
            'query': query, 'source_url': candidate['pauta_url'],
            'queue_checked_at': candidate['queue_checked_at'],
            'queue_reference_verified_at_selection': True,
            'queue_connection': candidate['connection'], 'evidence_storage': 'existing-private-homolog',
            'series_points': len(bundle['payload']['source']['interest_over_time']),
            'assessment': bundle['payload']['normalized']['assessment'],
            'exact_readback': True, 'human_query_review': 'PENDING',
            'commercial_status': 'UNKNOWN', 'queue_changed': False,
            'content_intent': (candidate.get('topic_proposal') or {}).get('content_intent'),
            'source_context': source_context}


def main():
    parser = argparse.ArgumentParser();parser.add_argument('mode', choices=('select', 'measure'))
    args = parser.parse_args()
    try:
        result = select() if args.mode == 'select' else measure()
        result['publication_authorized'] = False
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 2 if result.get('status') == 'BLOCKED' else 0
    except Exception as exc:
        reason=str(exc) if isinstance(exc,ValueError) and re.fullmatch('[A-Z0-9_]+',str(exc)) else type(exc).__name__
        print(json.dumps({'status':'BLOCKED','reason':reason}))
        return 1


if __name__=='__main__':raise SystemExit(main())
