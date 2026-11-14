import unittest
from unittest.mock import patch

from ops.hostinger import gate_stage_contract as gate


class GateContractInspectionTests(unittest.TestCase):
    def test_delegated_function_scanned_without_executing(self):
        source = """<?php
        function cxeg_write($request) {
            return cxeg_write_impl($request);
        }
        function cxeg_write_impl($request) {
            $data = $request->get_json_params();
            $intent = $data['intent'];
            $media = $data['featured_media'];
            return false;
        }
        function cxeg_permission($request) {
            return current_user_can('edit_posts');
        }"""
        results = gate.safe_contract(source)
        self.assertIn("cxeg_write_impl", results["cxeg_write"]["functions_followed"])
        self.assertIn("intent", results["cxeg_write"]["parameter_keys_seen"])
        self.assertIn("featured_media", results["cxeg_write"]["parameter_keys_seen"])
        self.assertIn("get_json_params", results["cxeg_write"]["request_accessors_seen"])

    def test_rest_index_tracks_truncation_not_route_failure(self):
        with patch.object(gate, "_fetch_index", side_effect=[
                (b'{"routes":', True, 200, "application/json"),
                (b'{"routes":{"/conexo/v1/editorial/write":{"endpoints":[{"methods":["POST"],"args":{"intent":{}}}]}}}', False, 200, "application/json")]):
            r = gate.index_probe()
        self.assertEqual(r[0]["diagnostic"], "response_truncated")
        self.assertTrue(r[1]["route_visible"])
        self.assertEqual(r[1]["public_args"], ["intent"])


if __name__ == "__main__":
    unittest.main()
