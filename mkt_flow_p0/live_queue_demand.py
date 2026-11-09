"""Choose a research candidate FROM the existing daily queue, read-only."""
import hashlib
import os
import re
from urllib.parse import urlsplit
from datetime import datetime, timezone
from mkt_flow_p0.opportunities import recent, instant

# Entity shapes, not a dated list of products or a demand/ranking heuristic.
ENTITY = re.compile(r'\b(?:Galaxy\s+(?:[SAMF]\d{1,3}(?:\s*(?:Ultra|Plus|FE|\+))?|Z\s*(?:Flip|Fold)\s*\d{1,2})|iPhone\s+(?:\d{1,2}(?:\s*(?:Pro\s+Max|Pro|Plus|Air|e))?|Air)|Pixel\s+\d{1,2}(?:\s*(?:Pro\s+XL|Pro|Fold|a))?|Nintendo\s+Switch(?:\s+\d)?|PlayStation\s+\d)(?![\w+])', re.I)


def connection_context():
    raw = os.getenv('TURSO_DATABASE_URL', '').strip()
    try:
        parsed = urlsplit(raw)
        if (parsed.scheme not in {'https', 'libsql'} or parsed.port is not None
                or parsed.username is not None or parsed.password is not None
                or parsed.path not in ('', '/') or parsed.query or parsed.fragment
                or not re.fullmatch(r'[a-z0-9-]+(?:\.[a-z0-9-]+)*\.turso\.io', parsed.hostname or '')
                or not os.getenv('TURSO_AUTH_TOKEN', '').strip()):
            raise ValueError('DAILY_CLOUD_CONNECTION_UNAVAILABLE')
    except ValueError:
        raise ValueError('DAILY_CLOUD_CONNECTION_UNAVAILABLE') from None
    return {'storage': 'turso', 'host_sha256': hashlib.sha256(parsed.hostname.encode()).hexdigest(),
            'configuration': 'same-repository-secrets-as-daily'}


def readonly_execute(sql, args=()):
    # Only fixed SELECTs issued by this module; no schema initialization/fallback.
    if not sql.startswith('SELECT ') or ';' in sql:
        raise ValueError('READONLY_SQL_REQUIRED')
    from mkt_flow_p0.cloud_db import turso_execute
    return turso_execute(sql, args)


def choose_existing(*, execute=None, now=None):
    context = connection_context()
    execute = execute or readonly_execute
    now = instant(now or datetime.now(timezone.utc))
    result = execute('SELECT name FROM sqlite_master WHERE type=? AND name=?', ('table', 'rss_pautas'))
    if not isinstance(result, dict) or 'erro' in result:
        raise ValueError('DAILY_QUEUE_SCHEMA_READ_FAILED')
    if result.get('rows') != [['rss_pautas']]:
        raise ValueError('DAILY_QUEUE_TABLE_NOT_FOUND')
    result = execute('SELECT id,url,titulo,publicada_em,estado FROM rss_pautas '
                     'WHERE estado=? AND fonte=? ORDER BY created_at DESC LIMIT 50',
                     ('DESCOBERTA', 'tecnoblog'))
    if not isinstance(result, dict) or 'erro' in result:
        raise ValueError('DAILY_QUEUE_READ_FAILED')
    rows = result.get('rows') or []
    excluded = {'stale_or_missing_date': 0, 'invalid_identity': 0, 'ambiguous_or_missing_entity': 0}
    for row in rows:
        if (not isinstance(row, (list, tuple)) or len(row) != 5
                or any(not isinstance(v, str) for v in row)):
            excluded['invalid_identity'] += 1
            continue
        uid, url, title, published, state = row
        try:
            parsed = urlsplit(url)
            port = parsed.port
        except ValueError:
            excluded['invalid_identity'] += 1
            continue
        if (not re.fullmatch('[0-9a-f]{32}', uid) or parsed.scheme != 'https'
                or parsed.hostname not in {'tecnoblog.net', 'www.tecnoblog.net'}
                or parsed.username is not None or parsed.password is not None or port is not None
                or parsed.fragment or state != 'DESCOBERTA' or hashlib.sha256(url.encode()).hexdigest()[:32] != uid):
            excluded['invalid_identity'] += 1
            continue
        if not recent(published, now, 168):
            excluded['stale_or_missing_date'] += 1
            continue
        matches = list(dict.fromkeys(m.group(0) for m in ENTITY.finditer(title)))
        if len(matches) != 1:
            excluded['ambiguous_or_missing_entity'] += 1
            continue
        return {'schema': 'conexo-live-queue-research-candidate/1', 'pauta_id': uid,
                'pauta_url': url, 'query': matches[0], 'published_at': published,
                'queue_checked_at': now.isoformat(), 'queue_reference_verified': True,
                'query_origin': 'exact_entity_substring_in_queue_title',
                'human_query_review': 'PENDING', 'commercial_status': 'UNKNOWN',
                'publication_authorized': False, 'queue_changed': False,
                'connection': context, 'rows_examined': len(rows), 'excluded': excluded}
    return {'status': 'BLOCKED', 'reason': 'NO_RECENT_UNAMBIGUOUS_ENTITY_IN_DAILY_QUEUE',
            'connection': context, 'rows_examined': len(rows), 'excluded': excluded,
            'queue_changed': False, 'publication_authorized': False}
