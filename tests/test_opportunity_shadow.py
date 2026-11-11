import copy
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from mkt_flow_p0.opportunity_shadow import compare

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cloud_probe', ROOT / 'scripts/cloud_editorial_probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ShadowTests(unittest.TestCase):
    def test_real_source_metadata_does_not_become_verified_demand_or_event(self):
        candidate = {'title': 'Fonte', 'url': 'https://example.org/source', 'kind': 'noticia',
                     'observed_at': '2026-11-09T12:00:00Z', 'published_at': '2026-11-09T11:00:00Z'}
        original = copy.deepcopy(candidate)
        result = compare([candidate], now='2026-11-09T12:00:00Z')
        self.assertEqual(candidate, original)
        self.assertEqual(result['counts'], {'DESCARTAR': 1})
        self.assertIn('DEMANDA_AUSENTE', result['reason_counts'])
        self.assertIn('FATO_FORA_DOS_7_DIAS_OU_SEM_DATA', result['reason_counts'])
        self.assertFalse(result['queue_changed'])
        self.assertFalse(result['publication_authorized'])

    def test_batch_bounded(self):
        for invalid in ({}, [None] * 101):
            with self.assertRaises(ValueError):
                compare(invalid)

    def test_run_reconstruction_is_exact_across_executors(self):
        first, second = probe.packet_for('123456789-1'), probe.packet_for('123456789-1')
        self.assertEqual(first, second)
        self.assertNotEqual(first, probe.packet_for('123456789-2'))
        self.assertFalse(first['publication_authorized'])

    def test_run_cannot_inject_payload(self):
        for invalid in ('', '../file', '1-1\n', 'a-1', '1-1;echo secret'):
            with self.assertRaises(ValueError):
                probe.packet_for(invalid)

    def test_configuration_blocks_before_database_import(self):
        for url in ('', 'libsql://production.turso.io', 'libsql://' + probe.HOST + '/path',
                    'libsql://user:pass@' + probe.HOST):
            with patch.dict(os.environ, {'TURSO_DATABASE_URL': url,
                                        'CONEXO_TRACE_TURSO_ALLOWED_HOST': probe.HOST,
                                        'TURSO_AUTH_TOKEN': 'fixture'}):
                with self.assertRaisesRegex(ValueError, 'BLOCKED_HOMOLOG_CONFIGURATION'):
                    probe.persistence('write', '123-1')

    def test_workflow_preserves_manual_free_and_independent_recovery(self):
        workflow = (ROOT / '.github/workflows/editorial-cloud-probe.yml').read_text()
        for required in ('github.event.repository.private == false',
                         'github.event.sender.login == github.repository_owner',
                         "'[cloud-probe] validar homolog e RSS real'", 'needs: write',
                         'environment: rss-homolog', 'permissions:\n  contents: read'):
            self.assertIn(required, workflow)
        for forbidden in ('schedule:', 'upload-artifact', 'cache:', 'WP_APP_PASSWORD', 'GROQ_API_KEY'):
            self.assertNotIn(forbidden, workflow)


if __name__ == '__main__':
    unittest.main()
