import unittest
from pathlib import Path
from unittest.mock import patch

from ops.hostinger import gate_issuer_discovery as discovery


class IssuerDiscoveryTests(unittest.TestCase):
    def test_finds_local_issuer_without_leaking_hmac_key(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            php = root / "includes" / "issuer.php"
            php.parent.mkdir()
            php.write_text("""<?php
            function cxeg_issue_receipt($payload) {
              $secret = 'NEVER_SHOW_REAL_SECRET';
              $signature = hash_hmac('sha256', json_encode($payload), $secret);
              return base64_encode(json_encode($payload));
            }
            function cxeg_decode($request) {
              $receipt = $request->get_param('receipt');
              return hash_equals('a', 'b');
            }
            """, encoding="utf-8")
            res = discovery.issuer_candidates(root)
            self.assertEqual(res[0]["functions"][0]["function"], "cxeg_issue_receipt")
            self.assertTrue(res[0]["functions"][0]["may_emit_receipt"])
            self.assertNotIn("NEVER_SHOW_REAL_SECRET", str(res))

    def test_ignores_random_large_file_without_execution(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "oversized.php").write_text("X" * 200001)
            with self.assertRaises(ValueError):
                discovery.issuer_candidates(root)


if __name__ == "__main__":
    unittest.main()
