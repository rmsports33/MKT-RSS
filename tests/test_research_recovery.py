import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mkt_flow_p0.queue_snapshot import export_queue, restore_queue
from mkt_flow_p0.research_signals import trends


class ResearchTests(unittest.TestCase):
    def test_provider_failure_is_unknown_without_leaking_response(self):
        def fail(*args, **kwargs):
            raise RuntimeError("secret must not appear")
        r = trends(["Celular"], provider=fail)
        self.assertEqual(r["status"], "INDISPONIVEL")
        self.assertIsNone(r["search_volume"])
        self.assertNotIn("secret", json.dumps(r))

    def test_provider_uses_br_full_window_and_no_browser(self):
        calls = []
        def provider(*args, **kwargs):
            calls.append((args, kwargs))
            return {"interest_over_time": []}
        r = trends(["A", "B"], provider=provider)
        self.assertEqual(calls[0][1], {"geo": "BR", "timeframe": "now 7-d", "engine": "http"})
        self.assertEqual(r["status"], "SNAPSHOT_NAO_VALIDADO")

    def test_autocomplete_empty_has_no_synthetic_demand(self):
        from mkt_flow_p0.keyword_research import pesquisar_keywords
        with patch("mkt_flow_p0.keyword_research._autocomplete", return_value=[]):
            r = pesquisar_keywords("A")
        self.assertEqual(r["keywords"], [])
        self.assertFalse(r["seven_day_demand_verified"])
        self.assertEqual(r["status"], "SEM_DADOS")


class QueueRecoveryTests(unittest.TestCase):
    def test_restore_after_executor_loss_preserves_editorial_state(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            original, snapshot, restored = p/"queue.db", p/"snapshot.db", p/"restored.db"
            with sqlite3.connect(original) as db:
                db.execute("CREATE TABLE rss_pautas(id TEXT, estado TEXT)")
                db.execute("INSERT INTO rss_pautas VALUES ('pauta-1','DESCOBERTA')")
            export_queue(original, snapshot)
            original.unlink()  # Disposable fixture only: simulate executor loss.
            result = restore_queue(snapshot, restored, str(snapshot)+".json")
            self.assertEqual(result["status"], "RESTAURADO")
            with sqlite3.connect(restored) as db:
                self.assertEqual(db.execute("SELECT * FROM rss_pautas").fetchall(), [("pauta-1", "DESCOBERTA")])
            before = hashlib.sha256(restored.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):
                restore_queue(snapshot, restored, str(snapshot)+".json")
            self.assertEqual(hashlib.sha256(restored.read_bytes()).hexdigest(), before)

    def test_corrupt_snapshot_is_rejected_before_creating_database(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            original, snapshot, restored = p/"queue.db", p/"snapshot.db", p/"restored.db"
            with sqlite3.connect(original) as db:
                db.execute("CREATE TABLE sample(value TEXT)")
            export_queue(original, snapshot)
            with snapshot.open("ab") as f:
                f.write(b"corrupted")
            with self.assertRaisesRegex(ValueError, "corrompido"):
                restore_queue(snapshot, restored, str(snapshot)+".json")
            self.assertFalse(restored.exists())


if __name__ == "__main__":
    unittest.main()
