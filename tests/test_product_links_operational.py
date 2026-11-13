"""Contrato produto↔pauta↔WordPress usando SQLite isolado, sem rede."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mkt_flow_p0.product_links import link_pauta, link_verified_draft, list_links
from mkt_flow_p0.fila_pautas import registrar
from mkt_flow_p0.product_catalog import load, identify_in_headline
import rss_queue_collect


class TestProductLinks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "queue.sqlite"
        self.a = {"titulo": "Motorola Signature 27 recebe atualização de bateria",
                  "link": "https://example.org/a", "fonte": "fixture",
                  "published": "2026-11-13"}
        self.b = {"titulo": "Nova falha de câmera afeta proprietários do Motorola Signature 27",
                  "link": "https://example.org/b", "fonte": "fixture",
                  "published": "2026-11-13"}

    def tearDown(self):
        self.temp.cleanup()

    def test_two_distinct_pautas_one_product_and_idempotence(self):
        first = registrar(self.a, db_path=self.db)
        second = registrar(self.b, db_path=self.db)
        self.assertNotEqual(first["id"], second["id"])
        for row, item in ((first, self.a), (second, self.b)):
            self.assertEqual(link_pauta("motorola-signature-27", row["id"], item["link"], self.db)["status"], "LINKED")
            link_pauta("motorola-signature-27", row["id"], item["link"], self.db)
        self.assertEqual(len(list_links("motorola-signature-27", self.db)), 2)

    def test_cannot_link_similar_headline_with_different_url(self):
        row = registrar(self.a, db_path=self.db)
        self.assertEqual(link_pauta("motorola-signature-27", row["id"], self.b["link"], self.db)["status"],
                         "SKIPPED_UNVERIFIED_QUEUE")
        self.assertEqual(list_links("motorola-signature-27", self.db), [])

    def test_verified_draft_create_update_and_conflict(self):
        row = registrar(self.a, db_path=self.db)
        link_pauta("motorola-signature-27", row["id"], self.a["link"], self.db)
        receipt = {"acao": "publicado_rascunho", "post_id": 9001,
                   "status": "draft", "wp_link": "https://conexotech.com.br/?p=9001"}
        self.assertEqual(link_verified_draft(self.a["link"], receipt, self.db)["status"], "DRAFT_LINKED")
        self.assertEqual(link_verified_draft(self.a["link"], receipt, self.db)["status"], "DRAFT_LINKED")
        self.assertEqual(list_links("motorola-signature-27", self.db)[0]["wp_post_id"], 9001)
        changed = dict(receipt, post_id=9002)
        self.assertEqual(link_verified_draft(self.a["link"], changed, self.db)["status"], "REVIEW_WP_POST_CONFLICT")
        self.assertEqual(list_links("motorola-signature-27", self.db)[0]["wp_post_id"], 9001)

    def test_no_authorization_from_unverified_wordpress(self):
        row = registrar(self.a, db_path=self.db)
        link_pauta("motorola-signature-27", row["id"], self.a["link"], self.db)
        for receipt in ({"acao": "publicado_rascunho", "post_id": 9001, "status": "publish"},
                        {"acao": "falha", "post_id": 9001, "status": "draft"},
                        {"acao": "publicado_rascunho", "post_id": None, "status": "draft"}):
            self.assertEqual(link_verified_draft(self.a["link"], receipt, self.db)["status"],
                             "SKIPPED_NOT_VERIFIED_DRAFT")
        self.assertIsNone(list_links("motorola-signature-27", self.db)[0]["wp_post_id"])
        self.assertFalse(link_pauta("motorola-signature-27", row["id"], self.a["link"], self.db)["publication_authorized"])

    def test_connection_failure_is_not_silently_recovered(self):
        row = registrar(self.a, db_path=self.db)
        with patch("mkt_flow_p0.product_links._exec", side_effect=RuntimeError("TURSO_UNAVAILABLE")):
            with self.assertRaisesRegex(RuntimeError, "TURSO_UNAVAILABLE"):
                link_pauta("motorola-signature-27", row["id"], self.a["link"], self.db)

    def test_rss_collector_links_only_after_registration_opt_in(self):
        feed = {"itens": [self.a]}
        from unittest.mock import patch
        with patch.dict(rss_queue_collect.FEEDS_PADRAO,
                        {"fixture": "https://example.invalid/feed"}, clear=True), \
             patch.dict(rss_queue_collect.os.environ,
                        {"CONEXO_PRODUCT_LINKS_ENABLED": "1"}), \
             patch.object(rss_queue_collect, "fetch_feed", return_value=feed), \
             patch.object(rss_queue_collect, "recent", return_value=True), \
             patch.object(rss_queue_collect, "registrar",
                          return_value={"id": "pauta1", "novo": True}), \
             patch("mkt_flow_p0.product_links.link_pauta",
                   return_value={"status": "LINKED"}) as link:
            result = rss_queue_collect.coletar(limite=1)
        link.assert_called_once_with("motorola-signature-27",
                                     "pauta1", "https://example.org/a")
        self.assertEqual(result["catalogo"]["vinculos"], 1)

    def test_rss_collector_no_link_without_opt_in(self):
        with patch.dict(rss_queue_collect.FEEDS_PADRAO,
                        {"fixture": "https://example.invalid/feed"}, clear=True), \
             patch.dict(rss_queue_collect.os.environ,
                        {"CONEXO_PRODUCT_LINKS_ENABLED": "0"}), \
             patch.object(rss_queue_collect, "fetch_feed",
                          return_value={"itens": [self.a]}), \
             patch.object(rss_queue_collect, "recent", return_value=True), \
             patch.object(rss_queue_collect, "registrar",
                          return_value={"id": "pauta1", "novo": True}), \
             patch("mkt_flow_p0.product_links.link_pauta") as link:
            result = rss_queue_collect.coletar(limite=1)
        link.assert_not_called()
        self.assertEqual(result["novas"], 1)

    def test_no_sqlite_fallback_without_cloud_credentials(self):
        with patch("mkt_flow_p0.product_links.cloud_db.turso_enabled",
                   return_value=False):
            with self.assertRaisesRegex(RuntimeError, "PRODUCT_LINK_CLOUD_CREDENTIALS_MISSING"):
                link_pauta("motorola-signature-27", "pauta1",
                           "https://example.org/a")
            with self.assertRaisesRegex(RuntimeError, "PRODUCT_LINK_CLOUD_CREDENTIALS_MISSING"):
                link_verified_draft("https://example.org/a",
                    {"acao": "publicado_rascunho", "post_id": 9001, "status": "draft"})

    def test_recognition_is_conservative(self):
        result = identify_in_headline(self.a["titulo"], load())
        self.assertEqual(result["product_id"], "motorola-signature-27")
        self.assertFalse(result["publication_authorized"])


if __name__ == "__main__":
    unittest.main()
