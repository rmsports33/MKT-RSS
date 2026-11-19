import tempfile
import unittest
from pathlib import Path

from mkt_flow_p0.fila_pautas import registrar
from mkt_flow_p0.conexo_discovery_adapter import exportar_candidatos


class DiscoveryAdapterTests(unittest.TestCase):
    def test_export_read_only_and_dedup(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "queue.sqlite"
            item = {"titulo": "Android recebe nova atualização de segurança",
                    "link": "https://example.org/noticia", "fonte": "teste"}
            first = registrar(item, db_path=db)
            second = registrar(item, db_path=db)
            result = exportar_candidatos(db_path=db)
            self.assertTrue(first["novo"])
            self.assertFalse(second["novo"])
            self.assertEqual(len(result["candidates"]), 1)
            self.assertEqual(result["candidates"][0]["pauta_id"], first["id"])
            self.assertFalse(result["publication_allowed"])
            self.assertFalse(result["approval"])
            self.assertTrue(result["candidates"][0]["requires_fact_check"])

    def test_invalid_limit_fails_closed(self):
        for limit in (0, 101, True, "20"):
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    exportar_candidatos(limit)


if __name__ == "__main__":
    unittest.main()
