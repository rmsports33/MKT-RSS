import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mkt_flow_p0.conexo_discovery_adapter import exportar_candidatos


class RSSReadOnlyRegressionTests(unittest.TestCase):
    def test_missing_sqlite_is_never_created(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "missing.sqlite"
            with self.assertRaises(FileNotFoundError):
                exportar_candidatos(db_path=db)
            self.assertFalse(db.exists())

    def test_turso_error_does_not_fallback_to_sqlite(self):
        with patch("mkt_flow_p0.conexo_discovery_adapter.cloud_db.turso_enabled", return_value=True), \
             patch("mkt_flow_p0.conexo_discovery_adapter.cloud_db.turso_execute", return_value={"erro": "offline"}):
            with self.assertRaisesRegex(RuntimeError, "offline"):
                exportar_candidatos()

    def test_turso_uses_only_select(self):
        rows = [["a" * 32, "feed", "https://example.org/x", "Android", "DESCOBERTA", 45]]
        with patch("mkt_flow_p0.conexo_discovery_adapter.cloud_db.turso_enabled", return_value=True), \
             patch("mkt_flow_p0.conexo_discovery_adapter.cloud_db.turso_execute", return_value={"rows": rows}) as execute:
            result = exportar_candidatos()
        self.assertEqual(len(result["candidates"]), 1)
        self.assertTrue(execute.call_args.args[0].lstrip().upper().startswith("SELECT"))
        self.assertFalse(result["publication_allowed"])


if __name__ == "__main__":
    unittest.main()
