import os
import unittest
from unittest.mock import patch

from mkt_flow_p0.editorial_trace import make_trace
from mkt_flow_p0.editorial_trace_turso import save_turso_trace, get_turso_trace


class TursoTraceTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "TURSO_DATABASE_URL": "libsql://mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io",
            "TURSO_AUTH_TOKEN": "mock-test-token",
            "CONEXO_TRACE_TURSO_ALLOWED_HOST": "mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.packet = make_trace("https://example.org/source", "generated article")

    def test_exact_host_guard(self):
        with patch.dict(os.environ, {"CONEXO_TRACE_TURSO_ALLOWED_HOST": "other.turso.io"}):
            self.assertEqual(save_turso_trace(self.packet, execute=lambda *a: {}),
                             {"ok": False, "reason": "TRACE_STORAGE_NOT_CONFIGURED"})

    def test_invalid_packet_has_no_database_side_effects(self):
        invalid = dict(self.packet)
        invalid.pop("article_id")
        def reject_write(*args, **kwargs):
            raise AssertionError("invalid packet attempted a database call")
        result = save_turso_trace(invalid, execute=reject_write)
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "TRACE_INVALID")

    def test_uses_parameterized_insert(self):
        calls = []
        def execute(sql, args=()):
            calls.append((sql, args))
            return {"affected": 1}
        result = save_turso_trace(self.packet, execute=execute)
        self.assertTrue(result["ok"])
        self.assertEqual(len(calls), 2)
        self.assertIn("VALUES (?,?,?,?,?,?)", calls[1][0])
        self.assertEqual(calls[1][1][0], self.packet["run_id"])
        self.assertIn("publication_authorized", calls[1][1][4])

    def test_timeout_never_retries(self):
        calls = []
        def execute(sql, args=()):
            calls.append(sql)
            return {"erro": "timeout"} if len(calls) == 2 else {"affected": 1}
        result = save_turso_trace(self.packet, execute=execute)
        self.assertFalse(result["ok"])
        self.assertEqual(len(calls), 2)
        self.assertEqual(result["reason"], "TRACE_INSERT_UNKNOWN_RECONCILE_BY_RUN_ID")

    def test_readback(self):
        from mkt_flow_p0.editorial_trace import json_trace
        def execute(sql, args=()):
            return {"rows": [[json_trace(self.packet)]]}
        result = get_turso_trace(self.packet["run_id"], execute=execute)
        self.assertTrue(result["ok"])
        self.assertEqual(result["trace"]["run_id"], self.packet["run_id"])


if __name__ == "__main__":
    unittest.main()
