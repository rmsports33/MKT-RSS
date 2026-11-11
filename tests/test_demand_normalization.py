import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
from mkt_flow_p0.demand_normalization import normalize_trends

NOW = datetime(2026, 11, 9, 16, 15, tzinfo=timezone.utc)


def source():
    start = NOW.replace(minute=0) - timedelta(days=7)
    return {'geo': 'BR', 'timeframe': 'now 7-d', 'fetched_at': NOW.isoformat(),
            'keywords': ['A', 'B'], 'interest_over_time': [
                {'date': (start + timedelta(hours=i)).isoformat(),
                 'values': {'A': 10, 'B': 0}, 'is_partial': False} for i in range(168)]}


class DemandNormalizationTests(unittest.TestCase):
    def test_exact_term_and_shared_group_without_mutating_source(self):
        raw = source(); before = copy.deepcopy(raw)
        a = normalize_trends(raw, 'A', now=NOW)
        b = normalize_trends(raw, 'B', now=NOW)
        self.assertEqual(raw, before)
        self.assertEqual(a['assessment']['status'], 'SINAL_OBSERVADO')
        self.assertEqual(b['assessment']['status'], 'SEM_SINAL_NA_AMOSTRA')
        self.assertEqual(a['demand']['comparison_group'], b['demand']['comparison_group'])
        self.assertEqual(a['demand']['query'], 'A')
        self.assertFalse(a['topic_relevance_verified'])
        self.assertFalse(a['publication_authorized'])

    def test_unrelated_query_or_wrong_region_cannot_supply_demand(self):
        with self.assertRaises(ValueError): normalize_trends(source(), 'Unrelated', now=NOW)
        raw=source(); raw['geo']='US'
        with self.assertRaises(ValueError): normalize_trends(raw, 'A', now=NOW)

    def test_partial_day_cannot_be_filled_with_zero_or_pass_coverage(self):
        raw=source()
        for row in raw['interest_over_time'][:24]: row['is_partial']=True
        result=normalize_trends(raw, 'A', now=NOW)
        self.assertEqual(result['excluded_points'],24)
        self.assertEqual(result['assessment']['status'],'NAO_VERIFICADA')

    def test_future_missing_flags_duplicates_and_invalid_values(self):
        raw=source(); raw['fetched_at']=(NOW+timedelta(hours=1)).isoformat()
        with self.assertRaises(ValueError): normalize_trends(raw,'A',now=NOW)
        raw=source(); del raw['interest_over_time'][0]['is_partial']
        with self.assertRaises(ValueError): normalize_trends(raw,'A',now=NOW)
        for bad in (101, float('nan'), True):
            raw=source();raw['interest_over_time'][0]['values']['A']=bad
            self.assertEqual(normalize_trends(raw,'A',now=NOW)['assessment']['status'],'NAO_VERIFICADA')
        raw=source();raw['interest_over_time'].append(raw['interest_over_time'][0])
        self.assertEqual(normalize_trends(raw,'A',now=NOW)['assessment']['status'],'NAO_VERIFICADA')

    def test_single_term_source(self):
        raw=source(); del raw['keywords'];raw['keyword']='A'
        for row in raw['interest_over_time']:row['value']=row.pop('values')['A']
        self.assertEqual(normalize_trends(raw,'A',now=NOW)['assessment']['status'],'SINAL_OBSERVADO')

    def test_workflow_has_no_schedule_secrets_storage_or_private_runner(self):
        workflow=(Path(__file__).resolve().parents[1]/'.github/workflows/demand-cloud-probe.yml').read_text()
        for expected in ('github.event.repository.private == false',
                         'github.event.sender.login == github.repository_owner',
                         "'[demand-probe] validar Trends BR 7 dias'", 'timeout-minutes: 3'):
            self.assertIn(expected,workflow)
        for forbidden in ('secrets.', 'schedule:', 'upload-artifact', 'cache:', 'environment:'):
            self.assertNotIn(forbidden,workflow)


if __name__ == '__main__': unittest.main()
