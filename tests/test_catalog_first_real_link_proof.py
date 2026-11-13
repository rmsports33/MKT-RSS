"""Primeiro vínculo RSS: teste sem rede, sem Turso, sem WordPress."""
import unittest
from unittest.mock import patch
from scripts.catalog_first_real_link_proof import proof


class ProductFirstRealProofTests(unittest.TestCase):
    def test_single_rss_item_and_authenticated_readback_contract(self):
        item = {"titulo": "Motorola Signature 27 tem bateria confirmada",
                "link": "https://example.org/moto-signature", "fonte": "gsmarena",
                "published": "2026-11-13"}
        with patch.dict("os.environ", {
                "TURSO_DATABASE_URL": "libsql://queue.turso.io",
                "TURSO_AUTH_TOKEN": "offline-mock",
                "CONEXO_PRODUCT_LINKS_ENABLED": "1",
             }), \\
             patch("scripts.catalog_first_real_link_proof.fetch_feed",
                   return_value={"itens": [item]}), \\
             patch("scripts.catalog_first_real_link_proof.recent", return_value=True), \\
             patch("scripts.catalog_first_real_link_proof.registrar",
                   return_value={"id": "queue-123", "novo": True}) as registrar, \\
             patch("scripts.catalog_first_real_link_proof.link_pauta",
                   return_value={"status": "LINKED",
                                 "publication_authorized": False}) as linked, \\
             patch("scripts.catalog_first_real_link_proof.cloud_db.turso_execute",
                   side_effect=[
                       {"rows": [["queue-123", "https://example.org/moto-signature",
                                  "DESCOBERTA", None, None]]},
                       {"rows": [["1"]]},
                   ]) as db:
            out = proof()
        self.assertEqual(out["result"], "PASS")
        self.assertFalse(out["publication_authorized"])
        self.assertFalse(out["wordpress_modified"])
        registrar.assert_called_once_with(item)
        linked.assert_called_once_with(
            "motorola-signature-27", "queue-123", item["link"])
        self.assertEqual(db.call_count, 2)

    def test_fails_closed_without_credentials(self):
        with patch.dict("os.environ", {"TURSO_DATABASE_URL": "",
             "TURSO_AUTH_TOKEN": "", "CONEXO_PRODUCT_LINKS_ENABLED": "1"}):
            with self.assertRaisesRegex(RuntimeError, "credentials unavailable"):
                proof()

    def test_fails_closed_without_link_readback(self):
        item = {"titulo": "Motorola Signature 27 tem bateria confirmada",
                "link": "https://example.org/moto-signature", "fonte": "gsmarena",
                "published": "2026-11-13"}
        with patch.dict("os.environ", {
                "TURSO_DATABASE_URL": "libsql://queue.turso.io",
                "TURSO_AUTH_TOKEN": "offline-mock",
                "CONEXO_PRODUCT_LINKS_ENABLED": "1",
             }), \\
             patch("scripts.catalog_first_real_link_proof.fetch_feed",
                   return_value={"itens": [item]}), \\
             patch("scripts.catalog_first_real_link_proof.recent", return_value=True), \\
             patch("scripts.catalog_first_real_link_proof.registrar",
                   return_value={"id": "queue-123", "novo": True}), \\
             patch("scripts.catalog_first_real_link_proof.link_pauta",
                   return_value={"status": "LINKED", "publication_authorized": False}), \\
             patch("scripts.catalog_first_real_link_proof.cloud_db.turso_execute",
                   return_value={"rows": []}):
            with self.assertRaisesRegex(RuntimeError, "readback not confirmed"):
                proof()


if __name__ == "__main__":
    unittest.main()
