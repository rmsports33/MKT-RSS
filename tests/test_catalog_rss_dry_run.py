"""Verificações do diagnóstico RSS somente leitura."""
import unittest
from unittest.mock import patch
import rss_queue_collect


class TestRSSDiagnostic(unittest.TestCase):
    def test_dry_run_classifies_without_queue_access(self):
        feed = {"itens": [
            {"titulo": "TCL C6K 65 tem novidades", "published": "2026-11-13"},
            {"titulo": "Roteador novo em teste", "published": "2026-11-13"},
        ]}
        with patch.dict(rss_queue_collect.FEEDS_PADRAO, {"fixture": "https://example.invalid/feed"}, clear=True), \
             patch.dict(rss_queue_collect.os.environ, {"CONEXO_REQUIRE_CLOUD_PERSISTENCE": "1", "TURSO_DATABASE_URL": "", "TURSO_AUTH_TOKEN": ""}), \
             patch.object(rss_queue_collect, "fetch_feed", return_value=feed), \
             patch.object(rss_queue_collect, "recent", return_value=True), \
             patch.object(rss_queue_collect, "registrar", side_effect=AssertionError("Não deve gravar")):
            outcome = rss_queue_collect.coletar(limite=2, dry_run=True)
        self.assertEqual(outcome["modo"], "DIAGNOSTICO_SEM_ESCRITA")
        self.assertEqual(outcome["analisadas"], 2)
        self.assertEqual(outcome["catalogo"]["correspondencias"], 1)
        self.assertEqual(outcome["catalogo"]["sem_correspondencia"], 1)
        self.assertEqual(outcome["novas"], 0)
        self.assertEqual(outcome["duplicadas"], 0)
        self.assertEqual(outcome["falhas"], [])

    def test_normal_mode_still_registers(self):
        feed = {"itens": [{"titulo": "TCL C6K 65", "published": "2026-11-13"}]}
        with patch.dict(rss_queue_collect.FEEDS_PADRAO, {"fixture": "https://example.invalid/feed"}, clear=True), \
             patch.object(rss_queue_collect, "fetch_feed", return_value=feed), \
             patch.object(rss_queue_collect, "recent", return_value=True), \
             patch.object(rss_queue_collect, "registrar", return_value={"novo": True}) as registrar:
            outcome = rss_queue_collect.coletar(limite=1)
        registrar.assert_called_once()
        self.assertEqual(outcome["novas"], 1)


if __name__ == "__main__":
    unittest.main()
