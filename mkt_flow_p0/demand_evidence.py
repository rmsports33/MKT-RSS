"""Private, immutable demand evidence. Stdlib only; hashes are not signatures."""
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from mkt_flow_p0.demand_normalization import normalize_trends
from mkt_flow_p0.opportunities import instant, demand_report, source_url

SCHEMA = 'conexo-demand-evidence/1'
MAX_BYTES = 512 * 1024


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def build(pauta_id, pauta_url, raw, query, *, now, review=None):
    if not isinstance(pauta_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', pauta_id):
        raise ValueError('INVALID_PAUTA_ID')
    if not source_url(pauta_url):
        raise ValueError('INVALID_PAUTA_URL')
    # Only the source series/context; never persist related claims, cookies or prompts.
    fields = ('geo', 'timeframe', 'fetched_at', 'keyword', 'keywords', 'interest_over_time')
    if not isinstance(raw, dict):
        raise ValueError('INVALID_SOURCE')
    source = json.loads(canonical({k: raw[k] for k in fields if k in raw}))
    terms = source.get('keywords', [source.get('keyword')])
    if (not isinstance(terms, list) or not 1 <= len(terms) <= 5
            or any(not isinstance(t, str) or not 1 <= len(t) <= 200 for t in terms)):
        raise ValueError('INVALID_SOURCE_TERMS')
    rows = source.get('interest_over_time')
    if not isinstance(rows, list) or len(rows) > 10000:
        raise ValueError('INVALID_SOURCE_SERIES')
    source['interest_over_time'] = [dict(
        date=row['date'], is_partial=row['is_partial'],
        **({'values': {t: row['values'][t] for t in terms}}
           if 'keywords' in source else {'value': row['value']})) for row in rows]
    if len(canonical(source).encode()) > 128 * 1024:
        raise ValueError('SOURCE_TOO_LARGE')
    evaluated_at = instant(now).isoformat()
    normalized = normalize_trends(source, query, now=evaluated_at)
    record = {'status': 'PENDING'}
    if review is not None:
        if (not isinstance(review, dict) or set(review) != {'reviewer', 'reason', 'reviewed_at'}
                or any(not isinstance(review[k], str) or not review[k].strip()
                       for k in ('reviewer', 'reason'))
                or len(review['reviewer']) > 128 or len(review['reason']) > 1000
                or not instant(source['fetched_at']) <= instant(review['reviewed_at']) <= instant(now)):
            raise ValueError('INVALID_QUERY_REVIEW')
        record = dict(review, status='DECLARED_NOT_AUTHENTICATED')
    payload = {'schema': SCHEMA, 'pauta_id': pauta_id, 'pauta_url': pauta_url,
               'query': query, 'source': source, 'normalized': normalized,
               'evaluated_at': evaluated_at, 'query_review': record,
               'queue_row_verified': False, 'publication_authorized': False}
    digest = hashlib.sha256(canonical(payload).encode()).hexdigest()
    bundle = {'sha256': digest, 'payload': payload}
    if len(canonical(bundle).encode()) > MAX_BYTES:
        raise ValueError('EVIDENCE_TOO_LARGE')
    return bundle


def verify(bundle):
    if not isinstance(bundle, dict) or set(bundle) != {'sha256', 'payload'}:
        raise ValueError('INVALID_EVIDENCE')
    if len(canonical(bundle).encode()) > MAX_BYTES:
        raise ValueError('EVIDENCE_TOO_LARGE')
    payload = bundle['payload']
    if hashlib.sha256(canonical(payload).encode()).hexdigest() != bundle['sha256']:
        raise ValueError('EVIDENCE_DIGEST_MISMATCH')
    if not isinstance(payload, dict) or payload.get('schema') != SCHEMA:
        raise ValueError('INVALID_EVIDENCE_SCHEMA')
    review = payload['query_review']
    if review == {'status': 'PENDING'}:
        declaration = None
    elif review.get('status') == 'DECLARED_NOT_AUTHENTICATED':
        declaration = {k: v for k, v in review.items() if k != 'status'}
    else:
        raise ValueError('INVALID_QUERY_REVIEW')
    rebuilt = build(payload['pauta_id'], payload['pauta_url'], payload['source'],
                    payload['query'], now=payload['evaluated_at'], review=declaration)
    if rebuilt != bundle:
        raise ValueError('EVIDENCE_REPLAY_MISMATCH')
    return payload


def replay(bundle, *, pauta_id, pauta_url, now=None):
    payload = verify(bundle)
    if (payload['pauta_id'], payload['pauta_url']) != (pauta_id, pauta_url):
        raise ValueError('PAUTA_ASSOCIATION_MISMATCH')
    return {'sha256': bundle['sha256'], 'exact_replay': True,
            'original_assessment': payload['normalized']['assessment'],
            'current_assessment': demand_report(payload['normalized']['demand'],
                instant(now or datetime.now(timezone.utc))),
            'query_review_status': payload['query_review']['status'],
            'queue_row_verified': False, 'publication_authorized': False}


def save_file(bundle, path):
    verify(bundle)
    data = canonical(bundle).encode()
    # Private exclusive create, including in ephemeral cloud runners.
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as stream:
        stream.write(data)
    return {'sha256': bundle['sha256'], 'bytes': len(data)}


def load_file(path):
    with Path(path).open('rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('EVIDENCE_TOO_LARGE')
    bundle = json.loads(data)
    verify(bundle)
    return bundle
