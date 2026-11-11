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


class StrictHTTP(FakeHTTP):
    def __init__(self, ready=True, finalized=True):
        super().__init__()
        self.ready, self.finalized = ready, finalized

    def get(self, url, **kwargs):
        if url.endswith('/seo-readiness'):
            self.gets.append(url)
            return Resp(200, {'schema': 'conexo-seo-readiness/1',
                **{k: self.ready for k in ('broker_signed_seo_supported', 'editorial_gate_ready',
                                         'seo_signing_ready', 'seo_public_output_ready')}})
        return super().get(url, **kwargs)

    def post(self, url, **kwargs):
        self.posts.append((url, kwargs))
        return Resp(200, {'post_id': POST_ID, 'intent': 'publish', 'version_sha256': VERSION,
            'status': 'publish', 'nonce': 'c' * 32,
            'snapshot': {'ID': POST_ID, 'post_status': 'publish', 'post_content': self.body},
            'publicacao_seo_concluidos': self.finalized,
            'seo_private_delivery': {'status': 'verified' if self.finalized else 'pending_inspection'}})


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
    def strict_run(self, http):
        seo = {'provider': 'native', 'canonical': 'https://conexotech.com.br/revisado/',
               'title': 'SEO revisto', 'description': 'Descricao revista.'}
        p = {**PACKAGE, 'payload': {**PACKAGE['payload'], 'seo': seo}}
        with patch('mkt_flow_p0.editorial_broker_transport.load_core', return_value=Core), \
             patch('mkt_flow_p0.editorial_broker_transport.require_release_trace'):
            return publish_via_broker(p, core_root='/unused', wp_url='https://conexotech.com.br',
                wp_user='svc', wp_password='test', trace_run_id=RUN, intent='publish',
                publication_reference='HUMAN-APPROVAL-SYNTHETIC', session=http, require_signed_seo=True)

    def test_strict_broker_checks_readiness_and_finishes_without_external_key(self):
        http = StrictHTTP()
        out = self.strict_run(http)
        self.assertTrue(out['publicacao_seo_concluidos'])
        sent = http.posts[0][1]['json']
        self.assertIs(sent['require_signed_seo'], True)
        self.assertEqual(len(sent['seo_sha256']), 64)
        self.assertNotIn('seo', sent)
        self.assertNotIn('signature', sent)
        self.assertEqual(len(http.posts), 1)

    def test_strict_broker_unready_never_publishes(self):
        http = StrictHTTP(ready=False)
        with self.assertRaisesRegex(BrokerBlocked, 'BROKER_SIGNED_SEO_NOT_READY'):
            self.strict_run(http)
        self.assertEqual(http.posts, [])

    def test_seo_failure_after_publication_returns_identity_without_retry(self):
        http = StrictHTTP(finalized=False)
        out = self.strict_run(http)
        self.assertIn('erro', out)
        self.assertEqual(out['post_id'], POST_ID)
        self.assertEqual(out['nonce'], 'c' * 32)
        self.assertIs(out['retry_automatic'], False)
        self.assertEqual(len(http.posts), 1)

    def test_transport_forwards_strict_mode_to_broker_without_signing_key(self):
        from mkt_flow_p0.editorial_transport import publish_package
        with patch.dict('os.environ', {'CONEXO_EDITORIAL_TRANSPORT': 'wp_broker',
                                      'CONEXO_REQUIRE_SIGNED_SEO': '1', 'CONEXO_EDITORIAL_GATE_KEY': ''}), \
             patch('mkt_flow_p0.editorial_broker_transport.publish_via_broker', return_value={'verified': True}) as broker:
            out = publish_package(PACKAGE, core_root='/unused', actor_id=4,
                wp_url='https://conexotech.com.br', wp_user='svc', wp_password='test', intent='publish')
        self.assertTrue(out['verified'])
        self.assertIs(broker.call_args.kwargs['require_signed_seo'], True)

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
        self.assertEqual(http.posts[0][1]["json"]["executor"], "mkt_rss")
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

    def test_broker_resume_never_repeats_write(self):
        from mkt_flow_p0.editorial_transport import publish_package
        with patch.dict("os.environ", {"CONEXO_EDITORIAL_TRANSPORT": "wp_broker"}), \
             patch("mkt_flow_p0.editorial_broker_transport.publish_via_broker") as broker:
            result = publish_package(
                PACKAGE, core_root="/unused", actor_id=7,
                wp_url="https://conexotech.com.br", wp_user="svc", wp_password="test",
                intent="publish", operation_nonce="a" * 32)
        self.assertIn("reconciliacao", result["reason"])
        broker.assert_not_called()

    def test_existing_publisher_forwards_turso_trace(self):
        from mkt_flow_p0.wp_publisher import publicar_no_wordpress
        package = {"payload": {"title": "Title", "content": CONTENT}}
        with patch("mkt_flow_p0.editorial_transport.publish_package",
                   return_value={"verified": True}) as publish:
            result = publicar_no_wordpress(
                "Title", CONTENT, "PASS", "https://conexotech.com.br", "svc", "test",
                status_desejado="publish", pacote_editorial=package,
                core_root="/unused", actor_id=7, trace_run_id=RUN,
                publication_reference="HUMAN-REFERENCE")
        self.assertTrue(result["verified"])
        self.assertEqual(publish.call_args.kwargs["trace_run_id"], RUN)


if __name__ == "__main__":
    unittest.main()
