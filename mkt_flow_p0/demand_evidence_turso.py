"""Opt-in private evidence table in existing Turso; never touches queue tables."""
import json
import os
import re
from mkt_flow_p0.demand_evidence import canonical, verify, MAX_BYTES


def configured():
    host = os.getenv('CONEXO_DEMAND_TURSO_ALLOWED_HOST', '').strip()
    return bool(re.fullmatch(r'[a-z0-9-]+(?:\.[a-z0-9-]+)*\.turso\.io', host)
                and os.getenv('TURSO_DATABASE_URL') == 'libsql://' + host
                and os.getenv('TURSO_AUTH_TOKEN', '').strip())


def _execute(sql, args=()):
    from mkt_flow_p0.cloud_db import turso_execute
    return turso_execute(sql, args)


def get(digest, *, execute=None):
    if not configured():
        return {'ok': False, 'reason': 'DEMAND_STORAGE_NOT_CONFIGURED'}
    if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
        return {'ok': False, 'reason': 'INVALID_EVIDENCE_ID'}
    result = (execute or _execute)(
        'SELECT payload_json FROM conexo_demand_evidence_v1 WHERE sha256=?', (digest,))
    if not isinstance(result, dict) or 'erro' in result:
        return {'ok': False, 'reason': 'DEMAND_READ_FAILED'}
    rows = result.get('rows') or []
    if len(rows) != 1 or len(rows[0]) != 1:
        return {'ok': False, 'reason': 'DEMAND_NOT_FOUND'}
    try:
        data = rows[0][0]
        if not isinstance(data, str) or len(data.encode()) > MAX_BYTES:
            raise ValueError('INVALID_PAYLOAD')
        bundle = json.loads(data)
        verify(bundle)
        if bundle['sha256'] != digest:
            raise ValueError('WRONG_EVIDENCE_ID')
    except (ValueError, TypeError, KeyError):
        return {'ok': False, 'reason': 'DEMAND_EVIDENCE_CORRUPT'}
    return {'ok': True, 'bundle': bundle}


def save(bundle, *, execute=None):
    # Validation before any schema/write operation. No local fallback.
    verify(bundle)
    if not configured():
        return {'ok': False, 'reason': 'DEMAND_STORAGE_NOT_CONFIGURED'}
    execute = execute or _execute
    result = execute('''CREATE TABLE IF NOT EXISTS conexo_demand_evidence_v1 (
        sha256 TEXT PRIMARY KEY, pauta_id TEXT NOT NULL, payload_json TEXT NOT NULL)''')
    if not isinstance(result, dict) or 'erro' in result:
        return {'ok': False, 'reason': 'DEMAND_SCHEMA_FAILED'}
    result = execute('''INSERT OR IGNORE INTO conexo_demand_evidence_v1
        (sha256,pauta_id,payload_json) VALUES (?,?,?)''',
        (bundle['sha256'], bundle['payload']['pauta_id'], canonical(bundle)))
    if not isinstance(result, dict) or 'erro' in result:
        # May have committed. Reconcile by digest explicitly, never retry blindly.
        return {'ok': False, 'reason': 'DEMAND_WRITE_UNKNOWN_RECONCILE_BY_DIGEST'}
    read = get(bundle['sha256'], execute=execute)
    if not read.get('ok') or read['bundle'] != bundle:
        return {'ok': False, 'reason': 'DEMAND_READBACK_FAILED'}
    return {'ok': True, 'sha256': bundle['sha256'], 'exact_readback': True}


def references(pauta_id, *, execute=None):
    """Read existing immutable versions by pauta. No schema/write or state change."""
    if not configured():
        return {'ok': False, 'reason': 'DEMAND_STORAGE_NOT_CONFIGURED'}
    if not isinstance(pauta_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', pauta_id):
        return {'ok': False, 'reason': 'INVALID_PAUTA_ID'}
    result = (execute or _execute)(
        'SELECT sha256 FROM conexo_demand_evidence_v1 WHERE pauta_id=? ORDER BY sha256 LIMIT 100',
        (pauta_id,))
    if not isinstance(result, dict) or 'erro' in result:
        return {'ok': False, 'reason': 'DEMAND_READ_FAILED'}
    rows = result.get('rows') or []
    if any(not isinstance(row, (list, tuple)) or len(row) != 1 or
           not isinstance(row[0], str) or not re.fullmatch('[0-9a-f]{64}', row[0]) for row in rows):
        return {'ok': False, 'reason': 'DEMAND_EVIDENCE_CORRUPT'}
    return {'ok': True, 'evidence_ids': [row[0] for row in rows]}
