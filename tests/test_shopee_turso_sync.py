"""Regressoes offline do sincronizador Shopee -> Turso homolog. Python 3.6+."""
import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

from mkt_flow_p0.price_evidence_turso import (
    TABLE, homolog_url_valid, load_local, sync,
)

HOST = "mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io"


class ShopeeTursoSyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "price_evidence.sqlite"
        self.prod = "Produto de teste"
        self.url = "https://shopee.com.br/product/42/777"
        self.fields = (self.prod, "shopee", "R$ 95,99", "13/11/2026", self.url)
        self.digest = hashlib.sha256("|".join(self.fields).encode("utf-8")).hexdigest()[:16]
        con = sqlite3.connect(str(self.path))
        con.execute("CREATE TABLE price_evidence (id INTEGER PRIMARY KEY, produto TEXT, "
                    "marketplace TEXT, preco_br TEXT, data_captura TEXT, "
                    "url_oferta TEXT, hash_evidencia TEXT)")
        con.execute("INSERT INTO price_evidence (produto,marketplace,preco_br,"
                    "data_captura,url_oferta,hash_evidencia) VALUES (?,?,?,?,?,?)",
                    self.fields + (self.digest,))
        con.commit()
        con.close()

    def tearDown(self):
        self.tmp.cleanup()

    def test_homolog_host_only(self):
        self.assertTrue(homolog_url_valid("libsql://" + HOST))
        self.assertTrue(homolog_url_valid("https://" + HOST))
        self.assertFalse(homolog_url_valid("libsql://mkt-rss-rmsports33.aws-ap-northeast-1.turso.io"))
        self.assertFalse(homolog_url_valid("https://" + HOST + ".attacker.test"))
        self.assertFalse(homolog_url_valid("https://" + HOST + "/other"))
        self.assertFalse(homolog_url_valid("https://" + HOST + "?token=unsafe"))
        self.assertFalse(homolog_url_valid("https://u:p@" + HOST))

    def test_local_load_readonly_and_consistent(self):
        rows = load_local(self.path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(tuple(rows[0][1:]), self.fields + (self.digest,))

    def test_reject_modified_local_hash(self):
        con = sqlite3.connect(str(self.path))
        con.execute("UPDATE price_evidence SET preco_br='R$ 96,00'")
        con.commit()
        con.close()
        with self.assertRaises(ValueError):
            load_local(self.path)

    def test_reject_invalid_marketplace_link(self):
        con = sqlite3.connect(str(self.path))
        con.execute("UPDATE price_evidence SET url_oferta='https://evil.test/'")
        con.commit()
        con.close()
        with self.assertRaises(ValueError):
            load_local(self.path)

    def test_missing_source_no_creation(self):
        target = Path(self.tmp.name) / "missing.sqlite"
        with self.assertRaises(ValueError):
            load_local(target)
        self.assertFalse(target.exists())

    def test_sync_insert_duplicate_and_independent_verify(self):
        rows = load_local(self.path)
        memory = {}
        def fake_execute(sql, args=()):
            if sql.startswith("CREATE TABLE"):
                return {"affected": 0}
            if sql.startswith("INSERT OR IGNORE"):
                if args[0] in memory:
                    return {"affected": 0}
                memory[args[0]] = tuple(args)
                return {"affected": 1}
            if sql.startswith("SELECT"):
                return {"rows": [list(memory[args[0]])] if args[0] in memory else []}
            raise AssertionError("Unexpected SQL")
        first = sync(rows, fake_execute, apply=True)
        second = sync(rows, fake_execute, apply=True)
        third = sync(rows, fake_execute, apply=False)
        self.assertEqual(first["new_remote_rows"], 1)
        self.assertEqual(second["new_remote_rows"], 0)
        self.assertEqual(third["exact_readback"], 1)

    def test_turso_failure_closed(self):
        rows = load_local(self.path)
        def fail(sql, args=()):
            if sql.startswith("CREATE TABLE"):
                return {"affected": 0}
            return {"erro": "connection lost"}
        self.assertEqual(sync(rows, fail, apply=True)["reason"],
                         "REMOTE_WRITE_UNKNOWN_RECONCILE")

    def test_turso_readback_mismatch_closed(self):
        rows = load_local(self.path)
        def bad(sql, args=()):
            if sql.startswith("CREATE TABLE") or sql.startswith("INSERT"):
                return {"affected": 1}
            return {"rows": [["corrupt"]]}
        self.assertEqual(sync(rows, bad, apply=True)["reason"],
                         "REMOTE_READBACK_MISMATCH")


if __name__ == "__main__":
    unittest.main()
