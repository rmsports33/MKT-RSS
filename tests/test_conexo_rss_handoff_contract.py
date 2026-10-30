"""Teste offline de interoperabilidade do exportador MKT-RSS.

Exercita banco SQLite real e o contrato de entrada do Conexo OS, sem rede.
"""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from mkt_flow_p0.fila_pautas import registrar
from mkt_flow_p0.conexo_discovery_export import main


class RSSHandoffContractTests(unittest.TestCase):
    def test_end_to_end_export_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "rss.sqlite"
            item = {"titulo": "Atualizacao Android de seguranca",
                    "link": "https://example.org/android", "fonte": "feed"}
            first = registrar(item, db_path=db)
            second = registrar(item, db_path=db)
            self.assertTrue(first["novo"])
            self.assertFalse(second["novo"])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["--db", str(db), "--limite", "20"])
            self.assertEqual(code, 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["schema"], "conexo-rss-discovery/1")
            self.assertIs(payload["read_only"], True)
            self.assertIs(payload["approval"], False)
            self.assertIs(payload["publication_allowed"], False)
            self.assertEqual(len(payload["candidates"]), 1)
            candidate = payload["candidates"][0]
            self.assertEqual(candidate["pauta_id"], first["id"])
            self.assertEqual(candidate["state"], "DESCOBERTA")
            self.assertIs(candidate["requires_fact_check"], True)
            self.assertIs(candidate["requires_editorial_decision"], True)

    def test_empty_queue_exports_no_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "rss.sqlite"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["--db", str(db)])
            self.assertEqual(code, 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["candidates"], [])
            self.assertIs(payload["publication_allowed"], False)


if __name__ == "__main__":
    unittest.main()
