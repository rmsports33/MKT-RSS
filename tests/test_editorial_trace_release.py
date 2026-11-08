import hashlib
import unittest
from unittest.mock import patch
from mkt_flow_p0.editorial_trace_gate import require_release_trace, REQUIRED
from mkt_flow_p0 import editorial_transport


def package():
    return {"payload": {
        "article_id": "9769",
        "content": "<p>A version-controlled private article</p>",
        "wordpress": {"post_id": 9769}
    }}


def complete_packet():
    p = package()
    return {
        "schema": "conexo-editorial-executor-events/1",
        "run_id": "trace-run-123",
        "article_id": p["payload"]["article_id"],
        "post_id": 9769,
        "content_sha256": hashlib.sha256(
            p["payload"]["content"].encode()).hexdigest(),
        "publication_authorized": False,
        "events": [
            {"stage": name, "status": "PASS",
             "evidence_ref": "proof_" + name, "module_id": "test"}
            for name in REQUIRED
        ]
    }


class TraceReleaseTests(unittest.TestCase):
    def test_trace_requires_matching_version_and_article(self):
        p = complete_packet()
        response = require_release_trace(
            package(), p["run_id"],
            lookup=lambda run_id: {"ok": True, "trace": p})
        self.assertTrue(response["trace_checked"])
        self.assertFalse(response["publication_authorized"])
        with self.assertRaisesRegex(ValueError, "version_mismatch"):
            require_release_trace(
                {**package(), "payload": {
                    **package()["payload"], "content": "<p>changed</p>"}},
                p["run_id"], lookup=lambda _: {"ok": True, "trace": p})

    def test_missing_review_blocks(self):
        p = complete_packet()
        p["events"] = [e for e in p["events"]
                       if e["stage"] != "editorial_approval"]
        with self.assertRaisesRegex(ValueError, "trace_incomplete"):
            require_release_trace(
                package(), p["run_id"], lookup=lambda _: {"ok": True, "trace": p})

    def test_unavailable_turso_blocks(self):
        with self.assertRaisesRegex(ValueError, "trusted_trace_unavailable"):
            require_release_trace(
                package(), "trace-run-123",
                lookup=lambda _: {"ok": False, "reason": "TRACE_NOT_FOUND"})

    def test_mkt_publisher_checks_trace_before_any_wordpress_network(self):
        class CanonicalValidator:
            HUMAN_PENDING = "human_pending"
            def evaluate(self, *args, **kwargs):
                return [], []
        class Core:
            def validator(self):
                return CanonicalValidator()
        with patch.dict("os.environ", {"CONEXO_REQUIRE_TRACE_FOR_PUBLICATION": "1"}):
            with patch.object(editorial_transport, "load_core", return_value=Core()):
                with patch.object(editorial_transport.requests, "get",
                                  side_effect=AssertionError("unexpected WP GET")) as get:
                    with patch.object(editorial_transport.requests, "post",
                                      side_effect=AssertionError("unexpected WP POST")) as post:
                        result = editorial_transport.publish_package(
                            package(), core_root=".", actor_id=4,
                            wp_url="https://conexotech.com.br",
                            wp_user="test", wp_password="test",
                            intent="publish", trace_run_id=None)
        self.assertEqual(result["erro"], "fluxo editorial bloqueado")
        self.assertIn("trace_run_id_missing", result["reason"])
        get.assert_not_called()
        post.assert_not_called()

    def test_private_draft_path_does_not_require_release_trace(self):
        class CanonicalValidator:
            HUMAN_PENDING = "human_pending"
            def evaluate(self, *args, **kwargs):
                return [], []
        class Core:
            def validator(self):
                return CanonicalValidator()
        with patch.dict("os.environ", {
            "CONEXO_REQUIRE_TRACE_FOR_PUBLICATION": "1",
            "CONEXO_EDITORIAL_GATE_KEY": "",
        }):
            with patch.object(editorial_transport, "load_core", return_value=Core()):
                result = editorial_transport.publish_package(
                    package(), core_root=".", actor_id=4,
                    wp_url="https://conexotech.com.br",
                    wp_user="test", wp_password="test",
                    intent="draft", trace_run_id=None)
        self.assertEqual(result["erro"], "fluxo editorial bloqueado")
        self.assertNotIn("trace_run_id_missing", result["reason"])
        self.assertIn("chave do executor ausente", result["reason"])


if __name__ == "__main__":
    unittest.main()
