"""Offline normalization of explicit Trends terms; no inferred keyword demand."""
import hashlib
import json
from datetime import timedelta
from urllib.parse import urlencode
from mkt_flow_p0.opportunities import instant, demand_report


def normalize_trends(raw, term, *, now):
    """Use last seven closed UTC hours/days; partial points never become zeros.

    Coverage is checked by the existing demand contract. The caller must still
    verify that the queried term actually represents the proposed article.
    """
    now = instant(now)
    if not isinstance(raw, dict) or raw.get('geo') != 'BR' or raw.get('timeframe') != 'now 7-d':
        raise ValueError('INVALID_TRENDS_CONTEXT')
    terms = raw.get('keywords') if 'keywords' in raw else [raw.get('keyword')]
    if not isinstance(terms, list) or term not in terms or not isinstance(term, str) or not term.strip():
        raise ValueError('QUERY_NOT_IN_SOURCE')
    fetched = instant(raw['fetched_at'])
    if fetched > now:
        raise ValueError('FUTURE_OBSERVATION')
    end = fetched.replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=7)
    points, excluded = [], 0
    rows = raw.get('interest_over_time')
    if not isinstance(rows, list) or len(rows) > 10000:
        raise ValueError('INVALID_TRENDS_SERIES')
    for row in rows:
        at = instant(row['date'])
        if type(row.get('is_partial')) is not bool:
            raise ValueError('PARTIAL_FLAG_REQUIRED')
        if row['is_partial'] or not start <= at < end:
            excluded += 1
            continue
        value = row['values'][term] if 'keywords' in raw else row['value']
        points.append({'at': at.isoformat(), 'value': value, 'partial': False})
    group = hashlib.sha256(json.dumps([terms, start.isoformat(), end.isoformat(),
                                     raw['fetched_at']], ensure_ascii=False).encode()).hexdigest()
    demand = {'source': 'trends', 'query': term, 'geo': 'BR',
              'source_url': 'https://trends.google.com/trends/explore?' + urlencode(
                  {'geo': 'BR', 'date': 'now 7-d', 'q': ','.join(terms)}),
              'period_start': start.isoformat(), 'period_end': end.isoformat(),
              'observed_at': fetched.isoformat(), 'comparison_group': group, 'points': points}
    return {'demand': demand, 'assessment': demand_report(demand, now),
            'excluded_points': excluded, 'topic_relevance_verified': False,
            'publication_authorized': False}
