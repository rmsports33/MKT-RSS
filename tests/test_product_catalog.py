import unittest
from mkt_flow_p0.product_catalog import load, match, register_candidate, identify_in_headline
from scripts.product_catalog_triage import triage

class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load()
    def test_eighteen_unique(self):
        self.assertEqual(len(self.catalog["products"]), 18)
    def test_existing_alias(self):
        self.assertEqual(match("TCL C6K 65", self.catalog)["product_id"], "tcl-c6k")
    def test_existing_case(self):
        self.assertEqual(match("  samsung Galaxy S26 FE ", self.catalog)["status"], "EXISTS")
    def test_unknown_is_not_automatically_approved(self):
        self.assertEqual(match("Novo Produto 999", self.catalog)["status"], "NEW_CANDIDATE")
    def test_no_duplicate_on_register(self):
        p = {"id":"samsung-galaxy-s26-fe","brand":"Samsung","model":"Galaxy S26 FE"}
        new, result = register_candidate(self.catalog, p)
        self.assertEqual(len(new["products"]), 18)
        self.assertEqual(result["status"], "EXISTS")
    def test_rss_headline_matches_known_product(self):
        result = identify_in_headline("TCL C6K 65 ganha nova oferta", self.catalog)
        self.assertEqual(result["product_id"], "tcl-c6k")
        self.assertFalse(result["publication_authorized"])
    def test_rss_unknown_headline_not_registered(self):
        self.assertEqual(identify_in_headline("Novo roteador Wi-Fi", self.catalog)["status"], "NO_MATCH")
    def test_offline_batch(self):
        result = triage(["TCL C6K 55", "TCL C6K 65", "Produto desconhecido"], self.catalog)
        self.assertEqual([r["status"] for r in result],
                         ["EXISTS", "EXISTS", "NEW_CANDIDATE"])
        self.assertEqual(result[0]["product_id"], result[1]["product_id"])
        self.assertTrue(all(r["publication_authorized"] is False for r in result))
    def test_offline_batch_invalid(self):
        self.assertEqual(triage([{"produto": ""}], self.catalog)[0]["status"], "REVIEW")
    def test_variants_preserved(self):
        p = next(p for p in self.catalog["products"] if p["id"] == "tcl-c6k")
        self.assertEqual({v["size_inches"] for v in p["variants"]}, {55, 65})

if __name__ == "__main__":
    unittest.main()
