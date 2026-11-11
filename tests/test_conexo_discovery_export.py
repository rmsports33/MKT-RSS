import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mkt_flow_p0.fila_pautas import registrar
from mkt_flow_p0.conexo_discovery_export import main


class RSSExportCLITests(unittest.TestCase):
    def test_export_from_sqlite_without_network(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "rss.sqlite"
            registrar({"titulo": "Noticia Android para revisao",
                       "link": "https://example.org/android", "fonte": "feed"}, db_path=db)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                status = main(["--db", str(db), "--limite", "5"])
            self.assertEqual(status, 0)
            packet = json.loads(out.getvalue())
            self.assertFalse(packet["publication_allowed"])
            self.assertEqual(len(packet["candidates"]), 1)
            self.assertEqual(packet["candidates"][0]["state"], "DESCOBERTA")

    def test_invalid_limit_does_not_emit_package(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = main(["--limite", "0"])
        self.assertEqual(status, 1)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("BLOCKED", err.getvalue())


if __name__ == "__main__":
    unittest.main()
