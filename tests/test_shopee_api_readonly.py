"""Regressões isoladas para consulta Shopee: sem rede ou segredos reais."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mkt_flow_p0 import price_collector as pc


class ShopeeReadOnlyTests(unittest.TestCase):
    def setUp(self):
        self.creds = {"partner_id": "12345", "partner_key": "segredo-mock"}
        self.node = {
            "itemId": 777, "shopId": 42, "productName": "Redmi Watch 6 Lite",
            "productLink": "https://shopee.com.br/product/42/777",
            "offerLink": "https://s.shopee.com.br/example",
            "price": "492.78", "priceMin": "492.78", "priceMax": "492.78", "shopName": "Loja Teste",
        }

    def _run(self, nodes=None, errors=None):
        response = type("Response", (), {
            "raise_for_status": lambda self: None,
            "json": lambda self: {"data": {"productOfferV2": {
                "nodes": [dict(self_node) for self_node in nodes]
            }}, "errors": errors} if errors else {
                "data": {"productOfferV2": {"nodes": list(nodes)}}},
        })()
        with patch.object(pc._CREDS, "shopee", self.creds), \
             patch.object(pc._CREDS, "tem_shopee", return_value=True), \
             patch.object(pc.requests, "post", return_value=response) as post:
            result = pc._coletar_shopee("777", "42")
        return result, post

    def test_valid_identity_and_signature(self):
        result, post = self._run([self.node])
        self.assertEqual(result["preco"], "492.78")
        self.assertEqual(result["nome"], "Redmi Watch 6 Lite")
        self.assertEqual(result["vendedor"], "Loja Teste")
        self.assertEqual(result["status"], "VERIFICADO_API_OFICIAL")
        self.assertEqual(post.call_count, 1)
        self.assertEqual(post.call_args.kwargs["timeout"], 15)
        self.assertIn(b"productOfferV2", post.call_args.kwargs["data"])
        self.assertNotIn(b"segredo-mock", post.call_args.kwargs["data"])
        self.assertTrue(post.call_args.kwargs["headers"]["Authorization"].startswith("SHA256 Credential="))

    def test_real_explorer_response_shape_without_credentials(self):
        # Exemplo público anonimizado do Explorer em 13/11/2026:
        # produto/loja e preços da resposta real; SEM segredo/API token.
        sample = {
            "itemId": 58217601055, "shopId": 728389176,
            "productName": "Parafusadeira Furadeira 1X Bateria 25V Nakasaki",
            "shopName": "MAQ TOOLS", "price": "95.99",
            "priceMin": "95.99", "priceMax": "95.99",
            "productLink": "https://shopee.com.br/product/728389176/58217601055",
            "offerLink": "https://s.shopee.com.br/public-example",
        }
        response = type("Response", (), {
            "raise_for_status": lambda self: None,
            "json": lambda self: {"data": {"productOfferV2": {
                "nodes": [sample]}}},
        })()
        with patch.object(pc._CREDS, "shopee", self.creds), \
             patch.object(pc._CREDS, "tem_shopee", return_value=True), \
             patch.object(pc.requests, "post", return_value=response) as post:
            result = pc._coletar_shopee(str(sample["itemId"]), str(sample["shopId"]))
        self.assertEqual(result["preco"], "95.99")
        self.assertEqual(result["origem"], "api_oficial_shopee")
        post.assert_called_once()

    def test_sqlite_pathlib_works_on_legacy_python(self):
        # sqlite3 do Python 3.6 do servidor requer str em vez de Path.
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "price_evidence.sqlite"
            with patch.object(pc, "_DB_PATH", db):
                inserted = pc._salvar_evidencia(
                    produto="Exemplo", marketplace="shopee",
                    preco_br="R$ 95,99", data_captura="13/11/2026",
                    url_oferta="https://shopee.com.br/product/42/777",
                    payload_bruto={"item_id": "777", "shop_id": "42"},
                )
            self.assertTrue(inserted)
            with sqlite3.connect(str(db)) as connection:
                rows = connection.execute(
                    "SELECT preco_br, marketplace FROM price_evidence"
                ).fetchall()
            self.assertEqual(rows, [("R$ 95,99", "shopee")])

    def test_wrong_item_rejected(self):
        result, _ = self._run([dict(self.node, itemId=888)])
        self.assertIsNone(result)

    def test_wrong_shop_rejected(self):
        result, _ = self._run([dict(self.node, shopId=888)])
        self.assertIsNone(result)

    def test_variable_price_rejected(self):
        result, _ = self._run([dict(self.node, priceMax="600.00")])
        self.assertIsNone(result)

    def test_inconsistent_current_price_rejected(self):
        result, _ = self._run([dict(self.node, price="490.00")])
        self.assertIsNone(result)

    def test_missing_current_price_rejected(self):
        result, _ = self._run([dict(self.node, price=None)])
        self.assertIsNone(result)

    def test_graphql_error_rejected(self):
        result, _ = self._run([self.node], [{"message": "not authorized"}])
        self.assertIsNone(result)

    def test_no_credentials_no_request(self):
        with patch.object(pc._CREDS, "tem_shopee", return_value=False), \
             patch.object(pc.requests, "post") as post:
            self.assertIsNone(pc._coletar_shopee("777", "42"))
            post.assert_not_called()

    def test_non_numeric_identifiers_no_request(self):
        with patch.object(pc._CREDS, "tem_shopee", return_value=True), \
             patch.object(pc.requests, "post") as post:
            self.assertIsNone(pc._coletar_shopee("777 or 1", "42"))
            post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
