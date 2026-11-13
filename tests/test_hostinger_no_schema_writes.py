"""Hardened queue runner must never issue schema migrations at runtime."""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mkt_flow_p0 import fila_pautas, product_links


class HardenedSchemaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "queue.sqlite"
        with sqlite3.connect(self.db) as con:
            con.execute(fila_pautas.SCHEMA)
            con.execute(fila_pautas.NOTAS_SCHEMA)
            con.execute(fila_pautas.MUTEX_SCHEMA)
            con.execute(product_links.SCHEMA)
        self.env = patch.dict(os.environ, {"CONEXO_RSS_SCHEMA_PREEXISTS": "1"})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_schema_preflight_existing_tables_only(self):
        sql = []
        original = fila_pautas._exec

        def inspect(stmt, *args, **kwargs):
            sql.append(stmt)
            return original(stmt, *args, **kwargs)

        with patch.object(fila_pautas, "_exec", side_effect=inspect):
            fila_pautas.init_queue(db_path=self.db)
        self.assertTrue(sql)
        self.assertTrue(all(s.strip().upper().startswith("SELECT ") for s in sql))

    def test_catalog_preflight_existing_table_only(self):
        sql = []
        original = product_links._exec

        def inspect(stmt, *args, **kwargs):
            sql.append(stmt)
            return original(stmt, *args, **kwargs)

        with patch.object(product_links, "_exec", side_effect=inspect):
            product_links._ensure(db_path=self.db)
        self.assertTrue(sql)
        self.assertTrue(all(s.strip().upper().startswith("SELECT ") for s in sql))

    def test_missing_table_must_fail_closed(self):
        with sqlite3.connect(self.db) as con:
            con.execute("DROP TABLE rss_notas_editoriais")
        with self.assertRaises(sqlite3.OperationalError):
            fila_pautas.init_queue(db_path=self.db)

    def test_normal_mode_still_initializes_schema(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.dict(os.environ, {"CONEXO_RSS_SCHEMA_PREEXISTS": "0"}):
                fila_pautas.init_queue(db_path=Path(d) / "fresh.sqlite")
                with sqlite3.connect(Path(d) / "fresh.sqlite") as con:
                    tables = {r[0] for r in con.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )}
                self.assertIn("rss_pautas", tables)


if __name__ == "__main__":
    unittest.main()
