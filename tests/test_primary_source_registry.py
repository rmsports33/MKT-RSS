import unittest

from mkt_flow_p0.primary_source_registry import (
    load_registry, classify_source_url, validate_source_record, validate_claim_record,
)


class RegistryTests(unittest.TestCase):
    def test_initial_registry_has_major_primary_source_entry_points(self):
        registry = load_registry()
        ids = {item["id"] for item in registry["sources"]}
        self.assertTrue({"br-epe","br-ons","br-aneel","br-ccee","br-anatel","br-mcom",
                         "br-ibge","global-iea","global-ember","us-eia","eu-eurostat",
                         "research-crossref","research-openalex","us-nist-nvd","us-sec-edgar"} <= ids)

    def test_known_source_is_only_a_discovery_hint_not_verified(self):
        result = classify_source_url("https://dados.ons.org.br/dataset/carga")
        self.assertEqual(result["source_id"], "br-ons")
        self.assertEqual(result["verification_status"], "NAO_VERIFICADA")
        self.assertTrue(result["factual_verification_required"])

    def test_unknown_gov_domain_does_not_become_primary_by_tld(self):
        result = classify_source_url("https://unknown.gov.example/document")
        self.assertIsNone(result["source_id"])
        self.assertEqual(result["suggested_role"], "discovery_lead")
        self.assertFalse(result["registry_match"])

    def test_http_and_userinfo_urls_rejected(self):
        for url in ("http://dados.ons.org.br/", "https://user:pass@dados.ons.org.br/"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                classify_source_url(url)

    def test_complete_claim_record_is_structural_only(self):
        sources = [{"source_id":"s1","source_role":"primary_origin"}]
        claim = {"claim_id":"c1","claim_text":"Carga verificada","source_ids":["s1"],
                 "source_role":"primary_origin","verification_status":"CONFIRMADA"}
        result = validate_claim_record(claim,sources)
        self.assertEqual(result["status"],"STRUCTURED_ONLY")
        self.assertFalse(result["factuality_verified"])

    def test_claim_with_unknown_source_fails(self):
        claim = {"claim_id":"c1","claim_text":"x","source_ids":["unknown"],
                 "source_role":"primary_origin","verification_status":"CONFIRMADA"}
        result = validate_claim_record(claim,[])
        self.assertEqual(result["status"],"INVALID")
        self.assertIn("CLAIM_SOURCE_REFERENCE_INVALID",result["errors"])

    def test_source_record_requires_locator_and_method_limits(self):
        source = {"source_id":"s1","url":"https://example.org/data","publisher":"Example",
                  "source_type":"dataset","source_role":"primary_origin","published_at":"2026-01-01",
                  "reference_period":"2025","locator":"Tabela 1","methodology":"metodo",
                  "limitations":"limites","retrieved_at":"2026-11-27"}
        self.assertEqual(validate_source_record(source),[])
        del source["locator"]
        self.assertIn("SOURCE_FIELD_MISSING:locator",validate_source_record(source))


if __name__ == "__main__":
    unittest.main()
