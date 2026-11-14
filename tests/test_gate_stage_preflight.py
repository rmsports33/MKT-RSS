import unittest
from unittest.mock import patch
from pathlib import Path

from ops.hostinger import gate_stage_preflight as gate


class GateStagePreflightTests(unittest.TestCase):
    def test_route_detection_structural_only(self):
        php = """register_rest_route('conexo/v1', '/editorial/write', array(
            'methods' => 'POST',
            'callback' => 'conexo_gate_stage_write',
            'permission_callback' => 'conexo_auth'
        ));"""
        r = gate.local_route_excerpt(php)
        self.assertEqual(r["status"], "FOUND_IN_PHP")
        self.assertEqual(r["route_mentions"], 1)

    def test_unknown_route_is_not_assumed_present(self):
        self.assertEqual(gate.local_route_excerpt("<?php return false;")["status"], "NOT_IDENTIFIED")

    def test_missing_plugin_blocks_and_never_calls_network(self):
        with patch.object(gate, "detect_file", return_value=(None, {"code": "MISSING"})):
            with patch.object(gate, "public_rest_probe") as network:
                self.assertEqual(gate.main(), 2)
                network.assert_not_called()

    def test_source_contains_no_write_calls(self):
        body = Path(gate.__file__).read_text(encoding="utf-8")
        self.assertNotIn("Request(url, data=", body)
        self.assertNotIn("wpcom_mcp_posts_create", body)
        self.assertNotIn("POST /", body)


if __name__ == "__main__":
    unittest.main()
