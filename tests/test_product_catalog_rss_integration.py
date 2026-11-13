"""Integração RSS x catálogo: sem rede, sem banco e sem WordPress."""
import unittest
from unittest.mock import patch
import rss_queue_collect


class CatalogCollectorTests(unittest.TestCase):
    def test_collect_counts_match_and_preserves_registration(self):
        feed = {"itens": [
            {"titulo": "TCL C6K 65 recebe atualização", "published": "2026-11-12"},
            {"titulo": "Novo roteador de fibra", "published": "2026-11-12"},
        ]}
        with patch.dict(rss_queue_collect.FEEDS_PADRAO, {"fixture": "https://example.invalid/feed"}, clear=True), \
             patch.object(rss_queue_collect, "fetch_feed", return_value=feed), \
             patch.object(rss_queue_collect, "recent", return_value=True), \
             patch.object(rss_queue_collect, "registrar", side_effect=[{"novo": True}, {"novo": False}]) as registrar:
            result = rss_queue_collect.coletar(limite=2)
        self.assertEqual(registrar.call_count, 2)
        self.assertEqual(result["novas"], 1)
        self.assertEqual(result["duplicadas"], 1)
        self.assertEqual(result["catalogo"]["correspondencias"], 1)
        self.assertEqual(result["catalogo"]["sem_correspondencia"], 1)
        self.assertFalse(result["falhas"])

    def test_catalog_unavailable_does_not_stop_collection(self):
        feed = {"itens": [{"titulo": "Notícia sem catálogo", "published": "2026-11-12"}]}
        with patch.dict(rss_queue_collect.FEEDS_PADRAO, {"fixture": "https://example.invalid/feed"}, clear=True), \
             patch.object(rss_queue_collect, "fetch_feed", return_value=feed), \
             patch.object(rss_queue_collect, "recent", return_value=True), \
             patch.object(rss_queue_collect, "load_product_catalog", side_effect=OSError("missing")), \
             patch.object(rss_queue_collect, "registrar", return_value={"novo": True}) as registrar:
            result = rss_queue_collect.coletar(limite=1)
        registrar.assert_called_once()
        self.assertTrue(result["catalogo"]["indisponivel"])
        self.assertEqual(result["novas"], 1)


if __name__ == "__main__":
    unittest.main()
