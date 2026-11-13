"""Regressões isoladas para consulta Shopee: sem rede ou segredos reais."""
import json
import unittest
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
