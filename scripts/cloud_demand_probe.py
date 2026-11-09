"""One real Trends comparison for exact RSS headlines; safe counters only."""
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.cloud_editorial_probe import rss_shadow
from mkt_flow_p0.research_signals import trends
from mkt_flow_p0.demand_normalization import normalize_trends


def main():
    rss_shadow()
    snapshot = json.loads(Path('shadow-real.json').read_text(encoding='utf-8'))
    # Exact source titles, no guessed product/entity extraction or silent truncation.
    terms = list(dict.fromkeys(i['title'] for i in snapshot['input']))[:3]
    if not terms or any(not 1 <= len(t) <= 200 for t in terms):
        raise ValueError('INVALID_SOURCE_TERMS')
    response = trends(terms)
    now = datetime.now(timezone.utc)
    result = {'schema': 'conexo-demand-cloud-probe/1', 'status': response['status'],
              'observed_at': now.isoformat(), 'geo': 'BR', 'term_count': len(terms),
              'term_selection': 'exact_rss_headlines_not_product_entities',
              'term_sha256': [hashlib.sha256(t.encode()).hexdigest() for t in terms],
              'queue_changed': False, 'publication_authorized': False,
              'market_search_volume': None}
    if response['status'] == 'SNAPSHOT_NAO_VALIDADO':
        normalized = [normalize_trends(response['raw'], term, now=now) for term in terms]
        # Ephemeral reviewed-import input, no artifacts or credentials.
        with open('demand-real.json', 'x', encoding='utf-8') as stream:
            json.dump(normalized, stream, ensure_ascii=False, allow_nan=False)
        result['assessments'] = [i['assessment'] for i in normalized]
        result['excluded_points'] = [i['excluded_points'] for i in normalized]
        result['topic_relevance_verified'] = False
    else:
        result['error_type'] = response.get('error_type')
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0 if response['status'] == 'SNAPSHOT_NAO_VALIDADO' else 2


if __name__ == '__main__':
    raise SystemExit(main())
