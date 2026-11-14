import hashlib
import re
import unittest
from pathlib import Path

from ops.hostinger.binance_editorial_review import enrich_review_payload, MANUSCRIPT_SHA
from mkt_flow_p0.editorial_core_offline import gerar_corpo_wordpress, gerar_html
from mkt_flow_p0.editorial_substance import assess_substance


ROOT = Path(__file__).resolve().parents[1]


class BinanceReviewedImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        article = (ROOT / "docs/ARTIGO_BINANCE_REVISAO_2026-11-14.md").read_text(encoding="utf-8")
        _, _, body = article.partition("\n")
        cls.body = re.sub(r"\n> \*\*Estado editorial:\*\*.*\Z", "", body, flags=re.S).strip()

    def test_review_bound_to_real_edit_and_with_no_human_approval(self):
        self.assertEqual(hashlib.sha256(self.body.encode()).hexdigest(), MANUSCRIPT_SHA)
        # Targeted regression only: AP 12/11 seizure is a subset of frozen funds.
        self.assertIn("mais de US$ 2,7 bilhões", self.body)
        self.assertIn("mais de US$ 1,2 bilhão", self.body)
        self.assertIn("Dentro desse total — e não como um valor adicional", self.body)
        self.assertIn("https://apnews.com/article/41be4834083e596a8facfd719f851cae", self.body)
        research = {"sources":[{"url":"https://example.org/news","facts":["Fato candidato pendente de revisão."]}]}
        payload = {"article": {"texto_markdown": self.body}, "research":research}
        enriched = enrich_review_payload(payload)
        self.assertEqual(enriched["editorial_voice_application"]["status"], "ASSISTED_ADAPTED")
        review = assess_substance(self.body, enriched["editorial_brief"],
                                  enriched["editorial_substance_review"])
        self.assertEqual(review["status"], "PASS")
        self.assertFalse(review["publication_authorized"])
        self.assertFalse(review["factual_approval"])
        self.assertEqual(enriched["editorial_contract"]["status"], "PENDING")
        self.assertEqual(enriched["editorial_contract"]["claims"][0]["evidence_ids"], [])
        with self.assertRaisesRegex(ValueError, "differs"):
            enrich_review_payload({"article":{"texto_markdown":self.body+" changed"},"research":research})

    def test_html_responsive_without_duplicate_source_sections(self):
        metadata = {
            "schema_version":"1.0", "article_id":"rss_binance_test",
            "status":"aguardando_revisao", "title":"Revisao Binance",
            "seo":{"title":"Revisao Binance","description":"Preview only","slug":"binance-revisao"},
            "sources":[{"name":"Example","url":"https://example.org/news"}],
            "claims":[], "review":{"approved":False},
        }
        body = gerar_corpo_wordpress(metadata,self.body)
        self.assertIn('conexo-table-scroll',body)
        self.assertIn('overflow-x:auto',body)
        self.assertEqual(body.count('<h2>Fontes</h2>'),0)
        self.assertNotIn('<h2>Leia também</h2><ul>',body)
        page = gerar_html(metadata,self.body)
        self.assertIn('max-width:920px',page)
        self.assertIn('noindex,nofollow',page)


if __name__=="__main__":
    unittest.main()
