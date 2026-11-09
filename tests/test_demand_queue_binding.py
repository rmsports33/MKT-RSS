import copy
import os
import sqlite3
import unittest
from unittest.mock import patch
from test_demand_evidence import ENV
from test_demand_normalization import source, NOW
from mkt_flow_p0.demand_evidence import build
from mkt_flow_p0.demand_queue_binding import check_binding


class DemandQueueBindingTests(unittest.TestCase):
    def setUp(self):
        self.bundle=build('pauta-1','https://example.org/source',source(),'A',now=NOW)
        self.db=sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        self.env=patch.dict(os.environ,ENV);self.env.start();self.addCleanup(self.env.stop)
        self.calls=[]

    def execute(self,sql,args=()):
        self.calls.append(sql)
        self.assertTrue(sql.startswith('SELECT '))
        cursor=self.db.execute(sql,args)
        return {'rows':[list(row) for row in cursor.fetchall()]}

    def create_row(self, url='https://example.org/source', title='A', state='DESCOBERTA'):
        self.db.execute('CREATE TABLE rss_pautas(id TEXT,url TEXT,titulo TEXT,estado TEXT)')
        self.db.execute('INSERT INTO rss_pautas VALUES (?,?,?,?)',('pauta-1',url,title,state))

    def test_exact_row_binding_without_approval_or_changes(self):
        self.create_row();before=self.db.total_changes
        result=check_binding(self.bundle,execute=self.execute)
        self.assertTrue(result['queue_row_verified'])
        self.assertEqual(result['query_relation'],'EXACT_QUEUE_TITLE')
        self.assertEqual(result['query_review_status'],'PENDING')
        self.assertFalse(result['topic_relevance_verified'])
        self.assertFalse(result['selection_authorized'])
        self.assertFalse(result['publication_authorized'])
        self.assertEqual(before,self.db.total_changes)
        self.assertEqual(len(self.calls),2)

    def test_missing_table_is_not_created(self):
        result=check_binding(self.bundle,execute=self.execute)
        self.assertEqual(result['reason'],'QUEUE_TABLE_NOT_FOUND')
        self.assertEqual(self.db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0],0)

    def test_missing_row_is_not_registered(self):
        self.create_row();self.db.execute('DELETE FROM rss_pautas');before=self.db.total_changes
        self.assertEqual(check_binding(self.bundle,execute=self.execute)['reason'],'QUEUE_ROW_NOT_FOUND')
        self.assertEqual(before,self.db.total_changes)

    def test_wrong_url_cannot_be_replaced_by_similar_title(self):
        self.create_row(url='https://example.org/other')
        self.assertEqual(check_binding(self.bundle,execute=self.execute)['reason'],'QUEUE_ID_URL_MISMATCH')

    def test_changed_title_keeps_review_pending_and_terminal_state_unchanged(self):
        self.create_row(title='Different',state='REJEITADA')
        result=check_binding(self.bundle,execute=self.execute)
        self.assertTrue(result['queue_row_verified'])
        self.assertEqual(result['query_relation'],'REPRESENTATIVENESS_REQUIRES_REVIEW')
        self.assertEqual(self.db.execute('SELECT estado FROM rss_pautas').fetchone()[0],'REJEITADA')
        self.assertFalse(result['selection_authorized'])

    def test_unconfigured_and_corrupt_evidence_make_no_calls(self):
        with patch.dict(os.environ,{'TURSO_AUTH_TOKEN':''}):
            self.assertEqual(check_binding(self.bundle,execute=self.execute)['reason'],'DEMAND_STORAGE_NOT_CONFIGURED')
        self.assertEqual(self.calls,[])
        broken=copy.deepcopy(self.bundle);broken['payload']['query']='changed'
        with self.assertRaises(ValueError):check_binding(broken,execute=self.execute)
        self.assertEqual(self.calls,[])

    def test_remote_failure_does_not_leak_messages_or_fallback(self):
        result=check_binding(self.bundle,execute=lambda *args:{'erro':'PRIVATE'})
        self.assertEqual(result['reason'],'QUEUE_SCHEMA_READ_FAILED')
        self.assertNotIn('PRIVATE',str(result))


if __name__=='__main__':unittest.main()
