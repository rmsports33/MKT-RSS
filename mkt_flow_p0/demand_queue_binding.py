"""Read-only evidence-to-queue checks. No registration, migration or approval."""
from datetime import datetime, timezone
from mkt_flow_p0.demand_evidence import verify
from mkt_flow_p0.demand_evidence_turso import configured


def check_binding(bundle, *, execute=None):
    payload = verify(bundle)
    base = {'schema': 'conexo-demand-queue-binding/1', 'sha256': bundle['sha256'],
            'checked_at': datetime.now(timezone.utc).isoformat(),
            'queue_row_verified': False, 'queue_changed': False,
            'query_review_status': payload['query_review']['status'],
            'topic_relevance_verified': False, 'publication_authorized': False}
    if not configured():
        return dict(base, status='BLOCKED', reason='DEMAND_STORAGE_NOT_CONFIGURED')
    if execute is None:
        from mkt_flow_p0.cloud_db import turso_execute
        execute = turso_execute
    schema = execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", ('rss_pautas',))
    if not isinstance(schema, dict) or 'erro' in schema:
        return dict(base, status='BLOCKED', reason='QUEUE_SCHEMA_READ_FAILED')
    if schema.get('rows') != [['rss_pautas']]:
        return dict(base, status='BLOCKED', reason='QUEUE_TABLE_NOT_FOUND')
    result = execute('SELECT id,url,titulo,estado FROM rss_pautas WHERE id=? LIMIT 2',
                     (payload['pauta_id'],))
    if not isinstance(result, dict) or 'erro' in result:
        return dict(base, status='BLOCKED', reason='QUEUE_READ_FAILED')
    rows = result.get('rows') or []
    if not rows:
        return dict(base, status='BLOCKED', reason='QUEUE_ROW_NOT_FOUND')
    if (len(rows) != 1 or not isinstance(rows[0], (list, tuple)) or len(rows[0]) != 4
            or any(not isinstance(value, str) for value in rows[0])):
        return dict(base, status='BLOCKED', reason='QUEUE_ROW_INVALID')
    uid, url, title, state = rows[0]
    # Queue registrar already stores canonical URLs. No title similarity fallback.
    if (uid, url) != (payload['pauta_id'], payload['pauta_url']):
        return dict(base, status='BLOCKED', reason='QUEUE_ID_URL_MISMATCH')
    if state not in {'DESCOBERTA', 'SELECIONADA', 'EM_PRODUCAO', 'EM_REVISAO',
                     'CONCLUIDA', 'REJEITADA', 'BLOQUEADA'}:
        return dict(base, status='BLOCKED', reason='QUEUE_STATE_INVALID')
    return dict(base, status='BINDING_VERIFIED', queue_row_verified=True,
                query_relation='EXACT_QUEUE_TITLE' if payload['query'] == title
                    else 'REPRESENTATIVENESS_REQUIRES_REVIEW',
                selection_authorized=False)
