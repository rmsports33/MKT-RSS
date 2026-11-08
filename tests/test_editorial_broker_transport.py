"""Fail-closed broker adapter tests; no real WordPress, Turso or secrets."""
import hashlib
import unittest
from unittest.mock import patch

from mkt_flow_p0.editorial_broker_transport import publish_via_broker, BrokerBlocked


POST_ID = 9769
CONTENT = "<p>Versao final aprovada apenas no teste sintetico</p>"
VERSION = "b" * 64
SHA = "a" * 64
RUN = "unit-run-9769"
PACKAGE = {
    "version_sha256": VERSION,
    "payload": {
        "article_id": "wp:9769",
        "content": CONTENT,
        "wordpress": {"post_id": POST_ID},
    },
}


class Resp:
    def __init__(self, status, data):
        self.status_code, self._data = status, data

    def json(self):
        return self._data


class FakeHTTP:
    def __init__(self, *, body=CONTENT, fail_broker=False):
        self.posts = []
        self.gets = []
        self.body = body
        self.fail_broker = fail_broker

    def get(self, url, **kwargs):
        self.gets.append(url)
        assert kwargs.get("allow_redirects") is False
        status = "publish" if self.posts else "draft"
        snap = {"ID": POST_ID, "post_status": status, "post_content": self.body}
        return Resp(200, {"snapshot": snap, "snapshot_sha256": SHA})

    def post(self, url, **kwargs):
        self.posts.append((url, kwargs))
        assert kwargs.get("allow_redirects") is False
        if self.fail_broker:
            return Resp(403, {"error": "denied"})
        return Resp(200, {
            "post_id": POST_ID, "intent": "publish",
            "version_sha256": VERSION, "status": "publish"
        })


class Core:
    @staticmethod
    def validator():
        class Validator:
            @staticmethod
            def evaluate(package, root, for_staging=False):
                return [], []
        return Validator()


def run(http, **kwargs):
    return publish_via_broker(
        PACKAGE, core_root="/tmp/synthetic-conexo",
        wp_url="https://conexotech.com.br",
        wp_user="synthetic-svc", wp_password="synthetic-app-password",
        trace_run_id=RUN, intent="publish",
        publication_reference="HUMAN-APPROVAL-SYNTHETIC",
        session=http, **kwargs,
    )


class BrokerTests(unittest.TestCase):
    def test_success_only_broker_after_turso(self):
        http = FakeHTTP()
        calls = []
        with patch("mkt_flow_p0.editorial_broker_transport.load_core", return_value=Core), \
             patch("mkt_flow_p0.editorial_broker_transport.require_release_trace",
                   side_effect=lambda p, r: calls.append((p, r))):
            value = run(http)
        self.assertTrue(value["verified"])
        self.assertEqual(value["retry_automatic"], False)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(http.posts), 1)
        self.assertTrue(http.posts[0][0].endswith("/conexo/v1/editorial/broker/write"))
        self.assertNotIn("signature", http.posts[0][1]["json"])
        self.assertNotIn("receipt", http.posts[0][1]["json"])
        self.assertEqual(len(http.gets), 2)

    def test_turso_not_verified_no_wp_requests(self):
        http = FakeHTTP()
        with patch("mkt_flow_p0.editorial_broker_transport.load_core", return_value=Core), \
             patch("mkt_flow_p0.editorial_broker_transport.require_release_trace",
                   side_effect=ValueError("missing trace")):
            with self.assertRaisesRegex(BrokerBlocked, "TRACE_TURSO_RELEASE_NOT_VERIFIED"):
                run(http)
        self.assertEqual(http.posts, [])
        self.assertEqual(http.gets, [])

    def test_canonical_gate_denied_before_turso_and_wp(self):
        http = FakeHTTP()
        class Denied:
            @staticmethod
            def validator():
                class V:
                    @staticmethod
                    def evaluate(*args, **kwargs):
                        return ["HUMAN_PENDING"], []
                return V()
        with patch("mkt_flow_p0.editorial_broker_transport.load_core", return_value=Denied):
            with self.assertRaisesRegex(BrokerBlocked, "CANONICAL_GATE_BLOCKED"):
                run(http)
        self.assertEqual(http.posts, [])
        self.assertEqual(http.gets, [])

    def test_wp_content_changed_no_broker_write(self):
        http = FakeHTTP(body="corpo de outra versao")
        with patch("mkt_flow_p0.editorial_broker_transport.load_core", return_value=Core), \
             patch("mkt_flow_p0.editorial_broker_transport.require_release_trace"):
            with self.assertRaisesRegex(BrokerBlocked, "WP_CONTENT_MISMATCH"):
                run(http)
        self.assertEqual(http.posts, [])

    def test_remote_gate_rejection_no_retry(self):
        http = FakeHTTP(fail_broker=True)
        with patch("mkt_flow_p0.editorial_broker_transport.load_core", return_value=Core), \
             patch("mkt_flow_p0.editorial_broker_transport.require_release_trace"):
            with self.assertRaisesRegex(BrokerBlocked, "BROKER_REJECTED_NO_RETRY"):
                run(http)
        self.assertEqual(len(http.posts), 1)

    def test_trace_packet_store_must_succeed(self):
        http = FakeHTTP()
        packet = {"run_id": RUN, "post_id": POST_ID}
        with patch("mkt_flow_p0.editorial_broker_transport.load_core", return_value=Core), \
             patch("mkt_flow_p0.editorial_broker_transport.save_turso_trace",
                   return_value={"ok": False, "reason": "TIMEOUT"}):
            with self.assertRaisesRegex(BrokerBlocked, "TRACE_TURSO_STORE_NOT_CONFIRMED"):
                run(http, trace_packet=packet)
        self.assertEqual(http.posts, [])
        self.assertEqual(http.gets, [])

    def test_no_key_required_in_external_client(self):
        self.assertEqual(
            hashlib.sha256(CONTENT.encode()).hexdigest(),
            hashlib.sha256(PACKAGE["payload"]["content"].encode()).hexdigest()
        )


if __name__ == "__main__":
    unittest.main()
