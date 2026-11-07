import tempfile
import unittest
from pathlib import Path

from mkt_flow_p0.editorial_trace import make_trace, save_trace, digest


class EditorialTraceTests(unittest.TestCase):
    def test_groq_generation_is_observed_but_style_not_certified(self):
        article = "An original article."
        packet = make_trace(
            "https://example.org/source", article,
            generated={"modelo": "observed-model", "texto_markdown": article,
                       "prompt_sha256": digest("actual prompt")},
        )
        self.assertEqual(packet["publication_authorized"], False)
        by_stage = {e["stage"]: e for e in packet["events"]}
        self.assertEqual(by_stage["generation"]["status"], "PASS")
        self.assertEqual(by_stage["generation"]["model_id"], "observed-model")
        self.assertEqual(by_stage["style_review"]["status"], "NOT_RUN")
        self.assertEqual(by_stage["seo_review"]["status"], "UNKNOWN")

    def test_failed_generation_never_implies_success(self):
        packet = make_trace("https://example.org/source", "", error="provider 429")
        self.assertEqual(packet["events"][0]["status"], "FAIL")
        self.assertNotIn("provider 429", str(packet))

    def test_wordpress_readback_requires_confirmation(self):
        p = make_trace("https://example.org/source", "text", post_id=9769)
        self.assertEqual(p["events"][-1]["status"], "UNKNOWN")
        q = make_trace("https://example.org/source", "text",
                       post_id=9769, wp_readback=True)
        self.assertEqual(q["events"][-1]["status"], "PASS")

    def test_persistent_sidecar_exclusive(self):
        p = make_trace("https://example.org/source", "text")
        with tempfile.TemporaryDirectory() as tmp:
            path = save_trace(p, tmp)
            self.assertTrue(Path(path).is_file())
            with self.assertRaises(FileExistsError):
                save_trace(p, tmp)

    def test_bad_post_id_rejected(self):
        with self.assertRaises(ValueError):
            make_trace("https://example.org/source", "text", post_id=True)


if __name__ == "__main__":
    unittest.main()
