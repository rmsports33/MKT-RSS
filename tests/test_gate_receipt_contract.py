import unittest
from ops.hostinger import gate_receipt_contract as gate


class ReceiptContractReadOnlyTests(unittest.TestCase):
    def test_extract_receipt_fields_and_delegation(self):
        php = """<?php
        function cxeg_write($request) {
          $receipt = $request->get_param('receipt');
          $signature = $request->get_param('signature');
          return cxeg_write_locked($request);
        }
        function cxeg_write_locked($request) {
          $data = $request->get_json_params();
          $intent = $data['intent'];
          $meta = $receipt['version_sha256'];
          if ($intent === 'stage') { return wp_insert_post([]); }
        }
        function cxeg_permission($request) {
          return current_user_can('edit_posts');
        }"""
        summary = gate.analyze(php)
        self.assertIn("receipt", summary["cxeg_write"]["fields_seen"])
        self.assertIn("signature", summary["cxeg_write"]["fields_seen"])
        self.assertIn("cxeg_write_locked", summary["cxeg_write"]["local_calls"])
        self.assertIn("intent", summary["cxeg_write_locked"]["fields_seen"])
        self.assertIn("stage", summary["cxeg_write_locked"]["literal_intents_seen"])
        self.assertIn("wp_insert_post", summary["cxeg_write_locked"]["control_tokens"])

    def test_secret_literals_and_unrelated_source_are_not_emitted(self):
        php = """<?php
        function cxeg_write($request) {
          $secret = 'SUPER_SECRET_TEST_VALUE_NEVER_EXPOSE';
          $password = $request->get_param('password');
          $receipt = $request->get_param('receipt');
          return false;
        }"""
        report = str(gate.analyze(php))
        self.assertNotIn("SUPER_SECRET_TEST_VALUE_NEVER_EXPOSE", report)
        self.assertNotIn("password", report)
        self.assertIn("receipt", report)


if __name__ == "__main__":
    unittest.main()
