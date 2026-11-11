import copy
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from test_demand_normalization import source, NOW
from mkt_flow_p0.demand_evidence import build, replay, verify, canonical, save_file, load_file
from mkt_flow_p0 import demand_evidence_turso as storage

ROOT = Path(__file__).resolve().parents[1]
HOST = 'mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io'
ENV = {'TURSO_DATABASE_URL': 'libsql://' + HOST, 'TURSO_AUTH_TOKEN': 'fixture',
       'CONEXO_DEMAND_TURSO_ALLOWED_HOST': HOST}


class DemandEvidenceTests(unittest.TestCase):
    def bundle(self):
        return build('pauta-1', 'https://example.org/source', source(), 'A', now=NOW)

    def test_full_series_replay_and_stale_current_assessment(self):
        bundle = self.bundle()
        result = replay(bundle, pauta_id='pauta-1', pauta_url='https://example.org/source',
                        now=NOW + timedelta(days=10))
        self.assertTrue(result['exact_replay'])
        self.assertEqual(result['original_assessment']['status'], 'SINAL_OBSERVADO')
        self.assertEqual(result['current_assessment']['status'], 'NAO_VERIFICADA')
        self.assertFalse(result['publication_authorized'])
        self.assertEqual(len(bundle['payload']['source']['interest_over_time']), 168)

    def test_wrong_pauta_and_modified_query_or_series_rejected(self):
        bundle = self.bundle()
        with self.assertRaisesRegex(ValueError, 'PAUTA_ASSOCIATION_MISMATCH'):
            replay(bundle, pauta_id='other', pauta_url='https://example.org/source')
        for field in ('query', 'series'):
            changed=copy.deepcopy(bundle)
            if field=='query': changed['payload']['query']='B'
            else: changed['payload']['source']['interest_over_time'][0]['values']['A']=99
            with self.assertRaisesRegex(ValueError, 'EVIDENCE_DIGEST_MISMATCH'): verify(changed)
            changed['sha256']=hashlib.sha256(canonical(changed['payload']).encode()).hexdigest()
            with self.assertRaisesRegex(ValueError, 'EVIDENCE_REPLAY_MISMATCH'): verify(changed)

    def test_review_is_declaration_and_not_an_authenticated_approval(self):
        review={'reviewer':'fixture-human', 'reason':'Explicit source association', 'reviewed_at':NOW.isoformat()}
        bundle=build('pauta-1','https://example.org/source',source(),'A',now=NOW,review=review)
        self.assertEqual(bundle['payload']['query_review']['status'],'DECLARED_NOT_AUTHENTICATED')
        self.assertFalse(bundle['payload']['publication_authorized'])
        review['reviewed_at']=(NOW+timedelta(hours=1)).isoformat()
        with self.assertRaises(ValueError):build('pauta-1','https://example.org/source',source(),'A',now=NOW,review=review)

    def test_unrelated_raw_metadata_does_not_get_persisted(self):
        raw=source(); raw['cookies']='PRIVATE';raw['related_queries']={'secret':'PRIVATE'}
        raw['interest_over_time'][0]['extra']='PRIVATE'
        bundle=build('pauta-1','https://example.org/source',raw,'A',now=NOW)
        self.assertNotIn('PRIVATE',canonical(bundle))

    def test_private_exclusive_file_survives_fresh_process_without_dependencies(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'private.json';save_file(self.bundle(),path)
            self.assertEqual(path.stat().st_mode & 0o777,0o600)
            before=path.read_bytes()
            with self.assertRaises(FileExistsError):save_file(self.bundle(),path)
            self.assertEqual(before,path.read_bytes())
            result=subprocess.run([sys.executable,'-S',str(ROOT/'demand_evidence.py'),'replay',
                '--input',str(path),'--pauta-id','pauta-1','--pauta-url','https://example.org/source',
                '--at',NOW.isoformat()],capture_output=True,text=True,cwd=folder,check=True)
            self.assertTrue(json.loads(result.stdout)['exact_replay'])
            path.write_text('x'*(512*1024+1))
            with self.assertRaisesRegex(ValueError,'EVIDENCE_TOO_LARGE'):load_file(path)

    def test_storage_guard_prevents_all_database_calls(self):
        def reject(*args):raise AssertionError('unexpected database access')
        for url in ('', 'libsql://other.turso.io', 'libsql://'+HOST+'/path'):
            with patch.dict(os.environ,dict(ENV,TURSO_DATABASE_URL=url)):
                self.assertEqual(storage.save(self.bundle(),execute=reject)['reason'],'DEMAND_STORAGE_NOT_CONFIGURED')

    def test_sql_storage_idempotence_recovery_and_corruption(self):
        # SQLite exercises parameterized statements but does NOT prove Turso real.
        with sqlite3.connect(':memory:') as db, patch.dict(os.environ,ENV):
            def execute(sql,args=()):
                cursor=db.execute(sql,args)
                return {'rows':[list(row) for row in cursor.fetchall()] if cursor.description else [],
                        'affected':cursor.rowcount}
            bundle=self.bundle()
            self.assertTrue(storage.save(bundle,execute=execute)['ok'])
            self.assertTrue(storage.save(bundle,execute=execute)['ok'])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM conexo_demand_evidence_v1').fetchone()[0],1)
            self.assertEqual(storage.get(bundle['sha256'],execute=execute)['bundle'],bundle)
            self.assertEqual(storage.references('pauta-1',execute=execute)['evidence_ids'],[bundle['sha256']])
            self.assertEqual(storage.references('other',execute=execute)['evidence_ids'],[])
            db.execute("UPDATE conexo_demand_evidence_v1 SET payload_json='{}'")
            self.assertEqual(storage.get(bundle['sha256'],execute=execute)['reason'],'DEMAND_EVIDENCE_CORRUPT')

    def test_unknown_write_never_retried_and_never_logs_remote_errors(self):
        calls=[]
        def execute(sql,args=()):
            calls.append(sql)
            return {} if len(calls)==1 else {'erro':'PRIVATE timeout after commit'}
        with patch.dict(os.environ,ENV):
            result=storage.save(self.bundle(),execute=execute)
        self.assertEqual(len(calls),2)
        self.assertEqual(result['reason'],'DEMAND_WRITE_UNKNOWN_RECONCILE_BY_DIGEST')
        self.assertNotIn('PRIVATE',json.dumps(result))

    def test_invalid_evidence_never_creates_schema(self):
        bundle=self.bundle();bundle['payload']['query']='tampered'
        with self.assertRaises(ValueError):storage.save(bundle,execute=lambda *a:self.fail('unexpected DB call'))

    def test_cloud_probe_is_manual_public_and_recovers_without_trends(self):
        workflow=(ROOT/'.github/workflows/demand-evidence-probe.yml').read_text()
        for expected in ('github.event.repository.private == false',
                         'github.event.sender.login == github.repository_owner',
                         "'[demand-evidence] guardar serie e reproduzir'", 'needs: store',
                         'environment: rss-homolog'):
            self.assertIn(expected,workflow)
        for forbidden in ('schedule:', 'upload-artifact', 'cache:', 'WP_APP_PASSWORD', 'GROQ_API_KEY'):
            self.assertNotIn(forbidden,workflow)
        recover=workflow.split('  recover:')[1]
        self.assertNotIn('trendspyg',recover)


if __name__=='__main__': unittest.main()
