"""WordPress-first adapter integration tests; fake API, no real site/secret."""
import json
import tempfile
from pathlib import Path
import unittest

from mkt_flow_p0.wp_quality_executor import WPReadError, WPClient, _NoRedirect, review_once, _private_db
from mkt_flow_p0.revisor_qualidade_unico import _sha


def post_fixture():
    return {
        "id": 9768, "status": "draft",
        "title": {"raw": "Android MCP: como agentes de IA vao conectar aplicativos"},
        "content": {"raw": (
            "<p>Google apresentou recurso experimental no Android.</p>" * 80 +
            '<p><a href="https://developer.android.com/ai/appfunctions">AppFunctions</a></p>' +
            '<a href="https://conexotech.com.br/android-drop-recursos-como-conferir/">1</a>' +
            '<a href="https://conexotech.com.br/microsoft-ia-altera-falas-labios-video-ao-vivo/">2</a>' +
            '<a href="https://conexotech.com.br/ceo-da-anthropic-pede-freio-na-ia-e-alerta-risco-online/">3</a>')},
        "excerpt": {"raw": "Texto de resumo editorial suficientemente longo sobre agentes de IA do Android e seus limites para usuários brasileiros."},
        "slug": "android-mcp-agentes-ia-conectar-aplicativos",
        "categories": [10], "featured_media": 9714,
    }


class FakeWP:
    def __init__(self, mutate=False):
        self.p = post_fixture()
        self.calls = 0
        self.mutate = mutate
        self.writes = []
    def post(self, post_id):
        self.calls += 1
        if self.mutate and self.calls == 2:
            self.p["title"]["raw"] += " mudanca"
        return json.loads(json.dumps(self.p))
    def media(self, _id):
        return {"id": 9714, "alt_text": "Android",
                "description": "Pexels license: https://www.pexels.com/license/"}
    def gate_snapshot(self, post_id):
        return {"snapshot_sha256": "a" * 64}
    def submit_quality(self, post_id, report, snapshot_sha):
        self.writes.append((post_id, snapshot_sha))
        return {"recorded": True}


class TestCloudAdapter(unittest.TestCase):
    def test_rascunho_realista_readonly_e_sqlite_privado(self):
        with tempfile.TemporaryDirectory() as root:
            client = FakeWP()
            report, remote = review_once(client, 9768, {}, str(Path(root) / "private.db"))
            self.assertEqual(report["post_id"], 9768)
            self.assertEqual(report["veredito"], "REVISAO_NECESSARIA")
            self.assertIsNone(remote)
            self.assertEqual(client.writes, [])
            self.assertTrue((Path(root) / "private.db").exists())
            import sqlite3
            with sqlite3.connect(str(Path(root) / "private.db")) as db:
                self.assertEqual(db.execute("select count(*) from quality_reviews").fetchone()[0], 1)

    def test_sqlite_symlink_is_rejected_without_touching_target(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "real.sqlite"
            target.write_bytes(b"preserve-this")
            link = Path(root) / "private.sqlite"
            link.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "Symlink DB forbidden"):
                _private_db(str(link))
            self.assertEqual(target.read_bytes(), b"preserve-this")

    def test_concurrent_edit_fails_before_save(self):
        with tempfile.TemporaryDirectory() as root:
            db = str(Path(root) / "private.db")
            with self.assertRaises(WPReadError):
                review_once(FakeWP(mutate=True), 9768, {}, db)
            self.assertFalse(Path(db).exists())

    def test_wrong_domain_and_url_components_fail_closed(self):
        for url in ("https://evil.invalid", "http://conexotech.com.br",
                    "https://conexotech.com.br:444", "https://conexotech.com.br/other",
                    "https://conexotech.com.br?redirect=1"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                WPClient(url, "editor", "test-app-password")

    def test_redirect_rejected_before_authorization_leaves_origin(self):
        handler = _NoRedirect()
        from urllib.request import Request
        with self.assertRaises(WPReadError):
            handler.redirect_request(Request("https://conexotech.com.br/wp-json/wp/v2/posts/1"),
                                     None, 302, "redirect", {}, "https://evil.invalid/steal")

    def test_published_post_never_generates_review_or_submission(self):
        with tempfile.TemporaryDirectory() as root:
            client = FakeWP()
            client.p["status"] = "publish"
            db = str(Path(root) / "report.db")
            with self.assertRaises(WPReadError):
                review_once(client, 9768, {}, db, submit_quality=True)
            self.assertFalse(Path(db).exists())
            self.assertEqual(client.writes, [])

    def test_no_remote_submission_of_partial_review(self):
        with tempfile.TemporaryDirectory() as root:
            client = FakeWP()
            with self.assertRaises(WPReadError):
                review_once(client, 9768, {}, str(Path(root) / "private.db"), submit_quality=True)
            self.assertEqual(client.writes, [])


if __name__ == "__main__":
    unittest.main()
