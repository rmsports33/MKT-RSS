import hashlib
import os
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch
from mkt_flow_p0.live_queue_demand import choose_existing, readonly_execute, connection_context, ENTITY

ENV={'TURSO_DATABASE_URL':'libsql://daily-fixture.turso.io','TURSO_AUTH_TOKEN':'fixture'}
NOW='2026-11-09T18:00:00Z'


class LiveQueueDemandTests(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,ENV);self.env.start();self.addCleanup(self.env.stop)
        self.db=sqlite3.connect(':memory:');self.addCleanup(self.db.close)
        self.db.execute('CREATE TABLE rss_pautas(id TEXT,url TEXT,titulo TEXT,publicada_em TEXT,estado TEXT,fonte TEXT,created_at TEXT)')
        self.calls=[]

    def row(self,title='Galaxy S26 Ultra tem novidades',published='2026-11-09T12:00:00Z',state='DESCOBERTA',url='https://tecnoblog.net/noticias/galaxy-s26-ultra/'):
        uid=hashlib.sha256(url.encode()).hexdigest()[:32]
        self.db.execute('INSERT INTO rss_pautas VALUES (?,?,?,?,?,?,?)',(uid,url,title,published,state,'tecnoblog',published))
        return uid

    def execute(self,sql,args=()):
        self.assertTrue(sql.startswith('SELECT '));self.assertNotIn(';',sql);self.calls.append(sql)
        return {'rows':[list(row) for row in self.db.execute(sql,args).fetchall()]}

    def test_same_actual_config_and_existing_identity_without_queue_write(self):
        uid=self.row();before=self.db.total_changes
        result=choose_existing(execute=self.execute,now=NOW)
        self.assertEqual(result['pauta_id'],uid)
        self.assertEqual(result['query'],'Galaxy S26 Ultra')
        self.assertTrue(result['queue_reference_verified'])
        self.assertFalse(result['queue_changed'])
        self.assertEqual(result['human_query_review'],'PENDING')
        self.assertEqual(result['commercial_status'],'UNKNOWN')
        self.assertNotIn('titulo',result);self.assertNotIn('fixture',str(result))
        self.assertEqual(self.db.total_changes,before)
        self.assertEqual(len(self.calls),2)

    def test_old_future_and_ambiguous_products_do_not_get_researched(self):
        for title,published in [('Galaxy S10','2026-10-01T12:00:00Z'),
                                ('iPhone 20','2026-11-10T12:00:00Z'),
                                ('Galaxy S26 ou iPhone 18','2026-11-09T12:00:00Z')]:
            with self.subTest(title=title):
                self.db.execute('DELETE FROM rss_pautas');self.row(title,published)
                self.assertEqual(choose_existing(execute=self.execute,now=NOW)['status'],'BLOCKED')

    def test_empty_queue_and_terminal_rows_are_not_inserted_or_promoted(self):
        for state in ('REJEITADA','CONCLUIDA','BLOQUEADA','EM_PRODUCAO'):
            self.row(state=state)
        before=self.db.total_changes
        result=choose_existing(execute=self.execute,now=NOW)
        self.assertEqual(result['reason'],'NO_RECENT_UNAMBIGUOUS_ENTITY_IN_DAILY_QUEUE')
        self.assertEqual(result['rows_examined'],0)
        self.assertEqual(self.db.total_changes,before)

    def test_no_private_credentials_url_or_fallback(self):
        for raw in ('','libsql://user:pass@daily-fixture.turso.io','http://daily-fixture.turso.io',
                    'libsql://daily-fixture.turso.io:443','libsql://127.0.0.1','libsql://daily-fixture.turso.io/path'):
            with patch.dict(os.environ,{'TURSO_DATABASE_URL':raw}):
                with self.assertRaisesRegex(ValueError,'DAILY_CLOUD_CONNECTION_UNAVAILABLE'):
                    choose_existing(execute=lambda *a:self.fail('Unexpected DB call'),now=NOW)
        for sql in ('CREATE TABLE anything(id TEXT)','SELECT 1; DELETE FROM rss_pautas'):
            with self.assertRaises(ValueError):readonly_execute(sql)

    def test_unrecognized_topic_exposes_only_already_published_source_reference(self):
        self.row(title='Assunto sem entidade reconhecida')
        result=choose_existing(execute=self.execute,now=NOW)
        self.assertEqual(result['status'],'BLOCKED')
        self.assertEqual(result['source_references'][0]['source_url'],'https://tecnoblog.net/noticias/galaxy-s26-ultra/')
        self.assertNotIn('Assunto',str(result))

    def test_existing_iphone_source_gets_explicit_evergreen_proposal_without_fake_approval(self):
        from mkt_flow_p0.live_queue_demand import TOPIC_PROPOSALS
        url=next(iter(TOPIC_PROPOSALS))
        uid=self.row(title='iPhone tem lista de palavras',url=url)
        result=choose_existing(execute=self.execute,now=NOW)
        self.assertEqual(result['pauta_id'],uid)
        self.assertEqual(result['query'],'teclado do iPhone')
        self.assertEqual(result['topic_proposal']['content_intent'],'evergreen_keyboard_guide')
        self.assertEqual(result['human_query_review'],'PENDING')
        self.assertFalse(result['publication_authorized'])

    def test_wrong_url_or_id_does_not_become_verified(self):
        self.row();self.db.execute("UPDATE rss_pautas SET url='https://other.example/article'")
        self.assertEqual(choose_existing(execute=self.execute,now=NOW)['status'],'BLOCKED')
        self.db.execute("UPDATE rss_pautas SET url='https://tecnoblog.net/different/'")
        self.assertEqual(choose_existing(execute=self.execute,now=NOW)['status'],'BLOCKED')

    def test_literal_entity_variants_are_preserved_without_old_seed_list(self):
        for title,expected in [('Galaxy S26+ chegou','Galaxy S26+'),('Galaxy S26 Ultra','Galaxy S26 Ultra'),
                               ('iPhone 18 Pro Max','iPhone 18 Pro Max'),('Pixel 11 Pro XL','Pixel 11 Pro XL'),
                               ('WhatsApp Web recebe novidade','WhatsApp Web'),
                               ('Google Fotos atualiza ferramenta','Google Fotos'),
                               ('Gemini muda aplicativo','Gemini')]:
            self.assertEqual(ENTITY.search(title).group(0),expected)
        self.assertIsNone(ENTITY.search('iPhone 180'))

    def test_evidence_write_target_must_differ_and_selection_must_not_expire(self):
        import importlib.util
        import json
        from datetime import datetime, timezone
        from test_demand_evidence import HOST, ENV as HOMOLOG_ENV
        spec=importlib.util.spec_from_file_location('live_probe',Path(__file__).resolve().parents[1]/'scripts/live_queue_demand_probe.py')
        probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
        now=datetime.now(timezone.utc).isoformat()
        candidate={'schema':'conexo-live-queue-research-candidate/1',
                   'queue_reference_verified':True,'queue_changed':False,
                   'queue_checked_at':now,'published_at':now,
                   'connection':{'host_sha256':hashlib.sha256(HOST.encode()).hexdigest()}}
        with patch.dict(os.environ,dict(HOMOLOG_ENV,CANDIDATE_JSON=json.dumps(candidate))), \
             patch('mkt_flow_p0.research_signals.trends',side_effect=AssertionError('Network must not be called')):
            with self.assertRaisesRegex(ValueError,'EVIDENCE_TARGET_EQUALS_DAILY_DATABASE'):probe.measure()
            candidate['queue_checked_at']='2000-01-01T00:00:00Z'
            os.environ['CANDIDATE_JSON']=json.dumps(candidate)
            with self.assertRaisesRegex(ValueError,'QUEUE_REFERENCE_EXPIRED'):probe.measure()

    def test_refused_source_is_not_retried_or_approved_and_demand_is_independent(self):
        import importlib.util
        import json
        from datetime import datetime,timezone
        from test_demand_evidence import ENV as HOMOLOG_ENV
        from test_demand_normalization import source
        spec=importlib.util.spec_from_file_location('live_probe',Path(__file__).resolve().parents[1]/'scripts/live_queue_demand_probe.py')
        probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
        now=datetime.now(timezone.utc).isoformat()
        candidate={'schema':'conexo-live-queue-research-candidate/1','pauta_id':'fixture-id',
                   'pauta_url':'https://tecnoblog.net/noticias/source','query':'A',
                   'queue_reference_verified':True,'queue_changed':False,
                   'queue_checked_at':now,'published_at':now,
                   'connection':{'host_sha256':'different-daily-db'},
                   'topic_proposal':{'required_source_terms':['iphone','teclado'],'content_intent':'guide'}}
        saved=[]
        def save(bundle):saved.append(bundle);return {'ok':True}
        def get(digest):return {'ok':True,'bundle':saved[0]}
        with patch.dict(os.environ,dict(HOMOLOG_ENV,CANDIDATE_JSON=json.dumps(candidate))), \
             patch('mkt_flow_p0.public_source_context.verify_context',side_effect=ValueError('SOURCE_HTTP_403')) as fetch, \
             patch('mkt_flow_p0.research_signals.trends',return_value={'status':'SNAPSHOT_NAO_VALIDADO','raw':source()}) as trends, \
             patch('mkt_flow_p0.demand_evidence_turso.save',side_effect=save), \
             patch('mkt_flow_p0.demand_evidence_turso.get',side_effect=get):
            result=probe.measure()
        self.assertEqual(fetch.call_count,1);self.assertEqual(trends.call_count,1)
        candidate['topic_proposal']['source_refusal']={'reason':'SOURCE_HTTP_403','run':'prior-run'}
        saved.clear()
        with patch.dict(os.environ,dict(HOMOLOG_ENV,CANDIDATE_JSON=json.dumps(candidate))), \
             patch('mkt_flow_p0.public_source_context.verify_context',side_effect=AssertionError('Previously refused source must NOT be retried')) as prior_fetch, \
             patch('mkt_flow_p0.research_signals.trends',return_value={'status':'SNAPSHOT_NAO_VALIDADO','raw':source()}) as independent_trends, \
             patch('mkt_flow_p0.demand_evidence_turso.save',side_effect=save), \
             patch('mkt_flow_p0.demand_evidence_turso.get',side_effect=get):
            result=probe.measure()
        self.assertEqual(prior_fetch.call_count,0);self.assertEqual(independent_trends.call_count,1)
        self.assertFalse(result['source_context']['access_retried'])
        self.assertEqual(result['source_context']['reason'],'SOURCE_HTTP_403')
        self.assertFalse(result['source_context']['factuality_verified'])
        self.assertTrue(result['exact_readback']);self.assertFalse(result['queue_changed'])
        self.assertEqual(result['human_query_review'],'PENDING')

    def test_workflow_reads_actual_secrets_and_writes_only_homolog(self):
        workflow=(Path(__file__).resolve().parents[1]/'.github/workflows/live-queue-demand.yml').read_text()
        select,measure=workflow.split('  measure:')
        self.assertNotIn('environment:',select)
        self.assertIn('secrets.TURSO_DATABASE_URL',select)
        self.assertIn('github.event.sender.login == github.repository_owner',select)
        self.assertIn('github.event.repository.private == false',select)
        self.assertIn('environment: rss-homolog',measure)
        self.assertIn('TURSO_DATABASE_URL: libsql://mkt-rss-homolog-',measure)
        for forbidden in ('schedule:','upload-artifact','cache:','WP_APP_PASSWORD','GROQ_API_KEY'):
            self.assertNotIn(forbidden,workflow)


if __name__=='__main__':unittest.main()
