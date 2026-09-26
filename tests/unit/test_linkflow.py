"""
Testes unit — /link (linkflow). Sem rede, sem polling, sem escrita real.
pytest tests/unit/test_linkflow.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "admin"))

import linkflow as L

ESPERADOS_15 = [
    "Galaxy Watch Ultra 2", "Galaxy Watch 9 40mm Wi-Fi", "Galaxy Watch 9 44mm Wi-Fi",
    "Samsung S90F 55", "TCL P7K 55", "LG QNED85 55", "TCL C6K 55",
    "Samsung QN90F 55", "Samsung S85F 55", "LG OLED C5 55",
    "Asus Vivobook Go 15", "Lenovo IdeaPad Slim 3",
    "Tribit Stormbox Blast 1", "Tribit Stormbox Blast 2",
    "Keychron V6 Max",
]


def test_norm_url_ok():
    assert L.norm_url("https://www.amazon.com.br/dp/B0X") == "https://www.amazon.com.br/dp/B0X"
    assert L.norm_url("http://x.com/a?b=1") == "http://x.com/a?b=1"
    assert L.norm_url("shopee.com.br/produto/123") == "https://shopee.com.br/produto/123"
    assert L.norm_url("  https://a.com/x  ") == "https://a.com/x"


def test_norm_url_rejeita():
    assert L.norm_url("") is None
    assert L.norm_url("nao e url") is None
    assert L.norm_url("javascript:alert(1)") is None
    assert L.norm_url("ftp://x.com/a") is None
    assert L.norm_url("https://sem espaco.com/x") is None
    assert L.norm_url("http://") is None


def test_catalogo_15_produtos_unicos():
    todos = L.todos_produtos()
    assert len(todos) == 15
    assert len(set(todos)) == 15
    assert sorted(todos) == sorted(ESPERADOS_15)


def test_guias_lojas_colunas():
    assert sorted(L.GUIAS) == ["caixa_som", "notebook", "smartwatch", "teclado", "tv4k"]
    assert L.LOJAS == ["Shopee", "Mercado Livre", "KaBuM!", "Amazon", "Magazine Luiza"]
    assert [L.COL[l] for l in L.LOJAS] == ["B", "C", "D", "E", "F"]


class _Vals:
    def __init__(self, fake):
        self.f = fake
        self._ult = None

    def get(self, spreadsheetId=None, range=None):
        self._ult = ("get", range)
        return self

    def update(self, spreadsheetId=None, range=None, valueInputOption=None, body=None):
        self._ult = ("update", range, body)
        return self

    def execute(self):
        kind = self._ult[0]
        if kind == "get":
            rng = self._ult[1]
            if rng.endswith("!A:A"):
                return {"values": [["Produto"]] + [[p] for p in self.f["prods"]]}
            # 'ABA'!C5
            cel = rng.split("!")[1]
            return {"values": [[self.f["cells"].get(cel, "")]]}
        rng, body = self._ult[1], self._ult[2]
        cel = rng.split("!")[1]
        self.f["cells"][cel] = body["values"][0][0]
        return {}


class _Sheets:
    def __init__(self, fake):
        self.f = fake

    def spreadsheets(self):
        return self

    def values(self):
        return _Vals(self.f)


def _fake():
    return {"prods": list(ESPERADOS_15), "cells": {"E3": "https://antigo.com/x"}}


def test_le_celula_vazia_e_ocupada():
    svc = _Sheets(_fake())
    assert L.le_celula("Galaxy Watch 9 40mm Wi-Fi", "Amazon", svc) == "https://antigo.com/x"
    assert L.le_celula("Galaxy Watch 9 40mm Wi-Fi", "Shopee", svc) == ""


def test_grava_e_rele():
    f = _fake()
    svc = _Sheets(f)
    ok, lido = L.grava_link("Keychron V6 Max", "KaBuM!", "https://novo.com/k", svc)
    assert ok and lido == "https://novo.com/k"
    assert f["cells"]["D16"] == "https://novo.com/k"


def test_grava_sobrescreve_quando_pedido():
    f = _fake()
    svc = _Sheets(f)
    ok, lido = L.grava_link("Galaxy Watch 9 40mm Wi-Fi", "Amazon", "https://novo.com/a", svc)
    assert ok and lido == "https://novo.com/a"


def test_produto_fora_da_aba_e_loja_invalida():
    svc = _Sheets(_fake())
    try:
        L.le_celula("Produto Fantasma", "Amazon", svc)
        raise AssertionError("devia falhar")
    except ValueError:
        pass
    try:
        L.le_celula("Keychron V6 Max", "Loja X", svc)
        raise AssertionError("devia falhar")
    except ValueError:
        pass
