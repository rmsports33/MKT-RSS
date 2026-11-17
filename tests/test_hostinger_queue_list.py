"""Offline proof that the queue_list bridge action is read-only and bounded.

No network, Turso, WordPress, publication or scheduled job. The only Turso
call is a mocked fixed SELECT; no user input is interpolated into SQL.
"""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "ops/hostinger/remote_queue_bridge.py"
spec = importlib.util.spec_from_file_location("_queue_bridge", BRIDGE)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class QueueListReadOnly(unittest.TestCase):
    def test_select_is_fixed_constant_with_no_user_input(self):
        # A fixed statement with a constant state and LIMIT 20; no formatting.
        src = BRIDGE.read_text(encoding="utf-8")
        self.assertIn("WHERE estado = 'DESCOBERTA'", src)
        self.assertIn("ORDER BY created_at DESC LIMIT 20", src)
        # No dynamic SQL construction markers.
        self.assertNotIn("f\"SELECT", src)
        self.assertNotIn(".format(", src.split("def list_titles")[1].split("def collect")[0])

    def test_list_titles_normalizes_and_bounds_rows(self):
        fake_rows = [
            ["a" * 32, "Black Magalu: Motorola Edge 70 Pro", "tecnoblog", "DESCOBERTA", 7, "2026-11-16T10:00:00Z"],
            ["b" * 32, "CEOs pedem volta de Jensen Huang à Nvidia", "tecnoblog", "DESCOBERTA", 5, "2026-11-16T09:00:00Z"],
        ]
        with patch.object(bridge, "_configure"), \
             patch("mkt_flow_p0.cloud_db.turso_execute", return_value={"rows": fake_rows}) as exec_:
            payload = bridge.list_titles()
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["mode"], "READ_ONLY")
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["items"][0]["titulo"], "Black Magalu: Motorola Edge 70 Pro")
        self.assertEqual(payload["items"][0]["pontuacao"], 7)
        self.assertFalse(payload["wordpress_written"])
        self.assertFalse(payload["publication_authorized"])
        sql = exec_.call_args[0][0]
        self.assertIn("SELECT id, titulo", sql)
        self.assertIn("LIMIT 20", sql)

    def test_list_titles_rejects_unexpected_schema(self):
        with patch.object(bridge, "_configure"), \
             patch("mkt_flow_p0.cloud_db.turso_execute", return_value={"rows": [["only-one-column"]]}):
            with self.assertRaises(RuntimeError):
                bridge.list_titles()

    def test_list_titles_fails_closed_on_turso_error(self):
        with patch.object(bridge, "_configure"), \
             patch("mkt_flow_p0.cloud_db.turso_execute", return_value={"erro": "down"}):
            with self.assertRaises(RuntimeError):
                bridge.list_titles()

    def test_no_title_longer_than_cap(self):
        long_title = "X" * 1000
        fake = [["c" * 32, long_title, "tecnoblog", "DESCOBERTA", 0, None]]
        with patch.object(bridge, "_configure"), \
             patch("mkt_flow_p0.cloud_db.turso_execute", return_value={"rows": fake}):
            payload = bridge.list_titles()
        self.assertLessEqual(len(payload["items"][0]["titulo"]), 300)


if __name__ == "__main__":
    unittest.main()
