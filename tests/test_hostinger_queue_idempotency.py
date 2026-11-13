"""Offline proof of duplicate prevention and single-writer locking.

No network, Turso, WordPress, publication, or scheduled job.
"""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from mkt_flow_p0 import fila_pautas as queue


class OfflineQueueIdempotency(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "proof.sqlite"
        self.env = patch.dict(os.environ, {"TURSO_DATABASE_URL": "", "TURSO_AUTH_TOKEN": "",
                                          "CONEXO_RSS_SCHEMA_PREEXISTS": "0"})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_same_url_never_creates_second_pauta(self):
        item = {
            "fonte": "teste-offline",
            "titulo": "Novo recurso Android para usuários brasileiros",
            "link": "https://example.com/tecnologia/android-recurso?utm_source=rss",
            "published": "2026-11-13T12:00:00Z",
            "resumo": "Teste local da fila RSS, sem serviço externo",
        }
        first = queue.registrar(item, db_path=self.db)
        second = queue.registrar(dict(item, link="https://example.com/tecnologia/android-recurso"), db_path=self.db)
        self.assertTrue(first["novo"])
        self.assertFalse(second["novo"])
        self.assertEqual(first["id"], second["id"])
        with sqlite3.connect(self.db) as con:
            rows = con.execute("SELECT id, estado FROM rss_pautas").fetchall()
        self.assertEqual(rows, [(first["id"], "DESCOBERTA")])

    def test_existing_writer_prevents_second_lock(self):
        queue.init_queue(db_path=self.db)
        owner = queue._reserve_writer(db_path=self.db)
        try:
            with self.assertRaises(RuntimeError):
                queue._reserve_writer(db_path=self.db)
        finally:
            queue._release_writer(owner, db_path=self.db)
        next_owner = queue._reserve_writer(db_path=self.db)
        self.assertNotEqual(owner, next_owner)
        queue._release_writer(next_owner, db_path=self.db)


if __name__ == "__main__":
    unittest.main()
