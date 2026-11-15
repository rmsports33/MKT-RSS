"""Offline safety regressions for the Hostinger queue bridge; never reach Turso/WP."""
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ops.hostinger import remote_queue_bridge as bridge
from ops.hostinger import remote_controller as ctrl


class QueueBridgeTests(unittest.TestCase):
    def test_request_allowlist_and_old_review_contract(self):
        self.assertEqual(ctrl.validate_request({"schema": "conexo-remote-request/1",
            "job_id": "queue-snapshot-20261115", "action": "queue_snapshot",
            "article_ref": "rss-pautas"}), ("queue-snapshot-20261115", "queue_snapshot"))
        self.assertEqual(ctrl.validate_request({"schema": "conexo-remote-request/1",
            "job_id": "binance-review-20261114", "action": "binance_substantive_review",
            "article_ref": "binance-revisao-6e8da0b05713"})[1], "binance_substantive_review")
        for action, ref in (("queue_collect", "binance-revisao-6e8da0b05713"),
                            ("unknown", "rss-pautas"), ("queue_snapshot", "../../etc/passwd")):
            with self.subTest(action=action), self.assertRaises(ValueError):
                ctrl.validate_request({"schema": "conexo-remote-request/1",
                    "job_id": "queue-snapshot-20261115", "action": action, "article_ref": ref})

    def test_missing_credentials_block_before_any_network(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(bridge, "URL_FILE", Path(tmp) / "url"), \
             patch.object(bridge, "TOKEN_FILE", Path(tmp) / "token"), \
             patch.dict(os.environ, {"TURSO_DATABASE_URL": ""}, clear=True):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = bridge.main(["--collect"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out.getvalue())["status"], "BLOCKED")

    def test_no_symlinks_or_public_token_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "key"
            p.write_text("secret")
            p.chmod(0o644)
            with self.assertRaises(ValueError):
                bridge._read_private(p)
            p.chmod(0o600)
            self.assertEqual(bridge._read_private(p), "secret")
            alias = Path(tmp) / "alias"
            alias.symlink_to(p)
            with self.assertRaises(ValueError):
                bridge._read_private(alias)

    def test_endpoint_is_validated_no_external_hosts(self):
        self.assertEqual(bridge._trusted_turso_url("libsql://mkt-rss-prod.turso.io"),
                         "https://mkt-rss-prod.turso.io")
        for value in ["http://mkt-rss-prod.turso.io", "https://example.org",
                      "https://mkt-rss-homolog.turso.io", "https://mkt-rss-prod.turso.io/pwn"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                bridge._trusted_turso_url(value)

    def test_snapshot_select_only_and_propagate_db_failure(self):
        from mkt_flow_p0 import cloud_db
        with patch.object(cloud_db, "turso_execute", return_value={
                 "rows": [["DESCOBERTA", "3"], ["EM_REVISAO", "1"]]}) as query:
            result = bridge.snapshot()
        self.assertEqual(result["total"], 4)
        self.assertFalse(result["publication_authorized"])
        self.assertEqual(query.call_count, 1)
        self.assertTrue(query.call_args.args[0].upper().startswith("SELECT"))
        with patch.object(cloud_db, "turso_execute", return_value={"erro": "offline"}):
            with self.assertRaises(RuntimeError):
                bridge.snapshot()

    def test_bounded_collect_without_wordpress_or_llm(self):
        import rss_queue_collect
        with patch.object(rss_queue_collect, "coletar", return_value={
                 "novas": 2, "duplicadas": 1, "falhas": []}) as collect:
            result = bridge.collect()
        collect.assert_called_once_with(fonte="tecnoblog", limite=2, dry_run=False)
        self.assertEqual(result["new"], 2)
        self.assertFalse(result["wordpress_written"])
        self.assertFalse(result["publication_authorized"])

    def test_existing_legacy_receipt_is_migrated_without_replaying(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / "remote-control-receipt.json"
            job = Path(tmp) / "jobs.json"
            ctrl._atomic_receipt(old, {"job_id": "previous-job-123", "status": "PASS"})
            prior = ctrl._previous_receipt(job, old, "previous-job-123")
            self.assertEqual(prior["status"], "PASS")
            self.assertTrue(job.is_file())
            self.assertIsNone(ctrl._previous_receipt(Path(tmp) / "other.json", old,
                                                     "different-job-123"))

    def test_per_job_receipt_uses_secure_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "item.json"
            ctrl._atomic_receipt(path, {"status": "STARTED"})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(path.read_text())["status"], "STARTED")


if __name__ == "__main__":
    unittest.main()
