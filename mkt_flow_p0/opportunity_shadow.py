"""Additive diagnostics for supplied candidates; never selects or mutates a queue."""
from collections import Counter
from mkt_flow_p0.opportunities import evaluate


def compare(candidates, *, now=None):
    if not isinstance(candidates, list) or len(candidates) > 100:
        raise ValueError('expected at most 100 candidates')
    results = [evaluate(item, now=now) for item in candidates]
    return {
        'schema': 'conexo-opportunity-shadow/1',
        'counts': dict(Counter(row['status'] for row in results)),
        'reason_counts': dict(Counter(reason for row in results for reason in row['reasons'])),
        'results': results,
        'queue_changed': False,
        'publication_authorized': False,
    }
