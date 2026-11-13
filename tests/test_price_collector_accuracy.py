"""Regressão offline do normalizador de preços; nunca faz request ou escrita."""
import math
import unittest
from decimal import Decimal
from unittest.mock import patch

from mkt_flow_p0.price_collector import normalizar_preco, coletar_preco_produto


class PriceEvidenceTests(unittest.TestCase):
    def test_decimal_separator_and_thousands(self):
        cases = {
            "1234.56": "R$ 1.234,56",
            "1.234,56": "R$ 1.234,56",
            "R$ 1.234,56": "R$ 1.234,56",
            "1234,56": "R$ 1.234,56",
            "R$ 492,78": "R$ 492,78",
            1234.56: "R$ 1.234,56",
            Decimal("2299.90"): "R$ 2.299,90",
            1: "R$ 1,00",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(normalizar_preco(value), expected)

    def test_invalid_or_ambiguous_prices_are_rejected(self):
        values = [None, True, False, 0, -5, float("nan"), float("inf"),
                  "1.2.3", "1,234.56", "1.234,567", "1.234.56",
                  "R$ 5,00 e R$ 2,00", "grátis", "9999999999.00"]
        for value in values:
            with self.subTest(value=value):
                self.assertEqual(normalizar_preco(value), "")

    def test_no_provider_no_fabricated_price(self):
        # Nenhum provedor real está implementado: não permitir sucesso falso.
        with patch("mkt_flow_p0.price_collector._coletar_amazon", return_value=None):
            result = coletar_preco_produto("Redmi Watch 6 Lite", asin="B123456789")
        self.assertFalse(result.get("ok"))
        self.assertNotIn("preco_br", result)


if __name__ == "__main__":
    unittest.main()
