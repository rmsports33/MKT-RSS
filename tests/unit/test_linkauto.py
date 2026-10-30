"""
Testes unit — /link v2 (linkauto): deteccao pelo link + catalogo dinamico.
Sem rede (getter/requests falsos), Sheets falso, sem polling.
pytest tests/unit/test_linkauto.py -v
"""
import asyncio
import sys
import types
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "admin"))
for _m in ("telegram", "telegram.ext", "linkauto", "linkflow", "admin", "admin.bot"):
    _mod = sys.modules.get(_m)
    if _mod is not None and getattr(_mod, "_FAKE", False):
        del sys.modules[_m]

import linkauto as LA  # noqa: E402
import linkflow as LF  # noqa: E402


HTML_OG = ('<html><head><meta property="og:title" content="Tribit StormBox Blast 2 '
           'Caixa de Som Bluetooth 90W" /></head></html>')
HTML_OG_INV = ('<html><head><meta content="Keychron V6 Max Teclado" '
               'property="og:title" /></head></html>')
HTML_TITLE = "<html><head><title>Samsung Smart TV 50 Crystal UHD 4K U8000H</title></head></html>"
HTML_VAZIO = "<html><head></head><body>oi</body></html>"

MESTRE_ROWS = [
    ["tipo", "modelo", "especificacao", "marketplace", "link", "status"],
    ["Smart TV", "Samsung S90F 55", "", "Amazon", "pendente", ""],
    ["Smart TV", "Samsung S90F 55", "", "Shopee", "", ""],
    ["Smart TV", "Samsung Crystal U8600F", "", "Amazon", "", ""],
    ["Celular", "Galaxy A37 5G", "", "Amazon", "", ""],
]
CATALOGO = ["Samsung S90F 55", "TCL P7K 55", "Galaxy Watch Ultra 2",
            "Tribit Stormbox Blast 2", "Tribit Stormbox Blast 1",
            "Galaxy Watch 9 40mm Wi-Fi", "Keychron V6 Max",
            "Samsung Crystal U8600F", "Galaxy A37 5G"]


# ---------------------------------------------------------------- puras
def test_extrai_titulo_og_title():
    def get(url, headers=None, timeout=None, allow_redirects=None):
        return SimpleNamespace(text=HTML_OG, url=url + "/dp/X", status_code=200)
    d = LA.extrai_titulo("https://x.com/a", getter=get)
    assert d["titulo"].startswith("Tribit StormBox Blast 2")
    assert d["fonte"] == "og:title" and d["status"] == 200


def test_extrai_titulo_ordens_e_quedas():
    def get_inv(url, **k):
        return SimpleNamespace(text=HTML_OG_INV, url=url, status_code=200)
    assert LA.extrai_titulo("https://x.com/a", getter=get_inv)["fonte"] == "og:title"

    def get_t(url, **k):
        return SimpleNamespace(text=HTML_TITLE, url=url, status_code=200)
    d = LA.extrai_titulo("https://x.com/a", getter=get_t)
    assert d["titulo"].startswith("Samsung Smart TV 50") and d["fonte"] == "<title>"

    def get_v(url, **k):
        return SimpleNamespace(text=HTML_VAZIO, url=url, status_code=200)
    assert LA.extrai_titulo("https://x.com/a", getter=get_v)["titulo"] is None

    def boom(url, **k):
        raise TimeoutError("travou")
    d = LA.extrai_titulo("https://x.com/a", getter=boom)
    assert d["titulo"] is None and "travou" in d["status"]


def test_limpa_titulo():
    assert LA.limpa_titulo("A &quot;B&quot;  C") == 'A "B" C'
    assert len(LA.limpa_titulo("x" * 200)) == 90


def test_casa_modelo_fortes():
    assert LA.casa_modelo("Samsung S90F 55 OLED 2026", CATALOGO)["modelo"] == "Samsung S90F 55"
    r = LA.casa_modelo("Tribit StormBox Blast 2 Caixa 90W", CATALOGO)
    assert r["nivel"] == "forte" and r["modelo"] == "Tribit Stormbox Blast 2"
    r = LA.casa_modelo("Galaxy Watch Ultra 2 Titanium", CATALOGO)
    assert r["nivel"] == "forte" and r["modelo"] == "Galaxy Watch Ultra 2"
    # Blast 1 vs Blast 2: o numero decide
    r = LA.casa_modelo("Tribit Stormbox Blast 1", CATALOGO)
    assert r["modelo"] == "Tribit Stormbox Blast 1"


def test_casa_modelo_nao_confunde_modelo_errado():
    # U8000H NAO pode casar forte com U8600F (modelo diferente!)
    r = LA.casa_modelo("Samsung Smart TV 50 Crystal UHD 4K U8000H Xbox", CATALOGO)
    assert not (r["nivel"] == "forte" and r["modelo"] == "Samsung Crystal U8600F"), r
    r = LA.casa_modelo("parafusadeira 12v azul", CATALOGO)
    assert r["nivel"] == "nada" and r["modelo"] is None


def test_casa_modelo_fraco_exemplo():
    r = LA.casa_modelo("Galaxy Watch Ultra Titanium", CATALOGO)
    assert r["nivel"] == "fraco" and r["modelo"] == "Galaxy Watch Ultra 2", r


def test_detecta_loja():
    casos = [("https://link.amazon/ABC", "Amazon"),
             ("https://www.amazon.com.br/dp/X", "Amazon"),
             ("https://www.shopee.com.br/produto/1", "Shopee"),
             ("https://produto.mercadolivre.com.br/x", "Mercado Livre"),
             ("https://www.kabum.com.br/produto/1", "KaBuM!"),
             ("https://www.magazineluiza.com.br/x", "Magazine Luiza"),
             ("https://lojaqualquer.com/x", None),
             ("nao-url", None)]
    for url, esp in casos:
        assert LA.detecta_loja(url) == esp, url


def test_guess_tipo():
    casos = [("Samsung Smart TV 50 Crystal 4K", "Smart TV"),
             ("Galaxy Watch 9 40mm", "Smartwatch"),
             ("Galaxy S25 FE 5G", "Celular"),
             ("iPhone 18 Pro 256GB", "Celular"),
             ("Asus Vivobook Go 15", "Notebook"),
             ("Tribit StormBox Blast 2", "Caixa de som"),
             ("Keychron V6 Max", "Teclado mecanico"),
             ("parafusadeira 12v", None)]
    for titulo, esp in casos:
        assert LA.guess_tipo(titulo) == esp, titulo


def test_parse_linhas_roundtrip():
    t = LA.msg_confirm("https://a.com/x", "Keychron V6 Max", "KaBuM!")
    d = LA.parse_linhas(t)
    assert d == {"url": "https://a.com/x", "modelo": "Keychron V6 Max", "loja": "KaBuM!"}
    assert LA.parse_linhas("sem nada") == {}


# ---------------------------------------------------------------- Sheets falso (mestre)
class _MVals:
    def __init__(self, f):
        self.f = f
        self._u = None

    def get(self, spreadsheetId=None, range=None):
        self._u = ("get", range)
        return self

    def update(self, spreadsheetId=None, range=None, valueInputOption=None, body=None):
        self._u = ("update", range, body)
        return self

    def append(self, spreadsheetId=None, range=None, valueInputOption=None,
               insertDataOption=None, body=None):
        self._u = ("append", range, body)
        return self

    def execute(self):
        k = self._u[0]
        if k == "get":
            rng = self._u[1]
            if rng.endswith("!A:F"):
                return {"values": [r[:] for r in self.f["rows"]]}
            import re as _re
            m = _re.search(r"!E(\d+)$", rng)
            return {"values": [[self.f["e"].get(int(m.group(1)), "")]]} if m else {"values": []}
        if k == "update":
            import re as _re
            m = _re.search(r"!E(\d+)$", self._u[1])
            self.f["e"][int(m.group(1))] = self._u[2]["values"][0][0]
            self.f["updates"].append(self._u[1])
            return {}
        self.f["rows"].append(self._u[2]["values"][0])
        self.f["appends"].append(self._u[2]["values"][0])
        return {}


class _MSheets:
    def __init__(self, f):
        self.f = f

    def spreadsheets(self):
        return self

    def values(self):
        return _MVals(self.f)


def _fake_mestre():
    return {"rows": [r[:] for r in MESTRE_ROWS], "e": {}, "updates": [], "appends": []}


@pytest.fixture(autouse=True)
def _base(monkeypatch):
    LA.limpa_cache_mestre()
    yield
    LA.limpa_cache_mestre()


def test_catalogo_tipos_e_linhas():
    cat = LA.catalogo_mestre(_MSheets(_fake_mestre()))
    assert sorted(cat["tipos"]) == ["Celular", "Smart TV"]
    assert cat["tipos"]["Smart TV"] == ["Samsung S90F 55", "Samsung Crystal U8600F"]
    assert cat["linhas"][("samsung s90f 55", "Amazon")]["row"] == 2


def test_grava_mestre_atualiza_e_rele():
    f = _fake_mestre()
    ok, det = LA.grava_mestre("Samsung S90F 55", "Amazon", "https://novo.com/x",
                              _MSheets(f))
    assert ok and det == "https://novo.com/x" and f["e"][2] == "https://novo.com/x"


def test_grava_mestre_sem_linha():
    f = _fake_mestre()
    assert LA.grava_mestre("Modelo Fantasma", "Amazon", "https://x.com", _MSheets(f)) == \
        (False, "sem-linha")


def test_cria_linha_com_revisar():
    f = _fake_mestre()
    assert LA.cria_linha_mestre("Smart TV", "Samsung U8000H", "Amazon", "https://x.com",
                                _MSheets(f)) is True
    assert f["appends"][-1] == ["Smart TV", "Samsung U8000H", "", "Amazon", "https://x.com",
                                "revisar"]


def test_roteador_guia_tab_mestre_e_criacao(monkeypatch):
    f = _fake_mestre()
    chamadas = []
    monkeypatch.setattr(LF, "grava_link",
                        lambda p, l, u: chamadas.append((p, l, u)) or (True, u))
    dest, ok, _det = LA.grava_destino("Keychron V6 Max", "KaBuM!", "https://x.com/y")
    assert dest == "guia" and ok and chamadas == [("Keychron V6 Max", "KaBuM!", "https://x.com/y")]
    dest, ok, _det = LA.grava_destino("Samsung Crystal U8600F", "Amazon", "https://x.com/a",
                                          svc=_MSheets(f))
    assert (dest, ok) == ("mestre", True)
    dest, ok, det = LA.grava_destino("Samsung U8000H", "Amazon", "https://x.com/b",
                                     svc=_MSheets(f))
    assert (dest, ok, det) == ("mestre", False, "falta-tipo")
    dest, ok, det = LA.grava_destino("Samsung U8000H", "Amazon", "https://x.com/b",
                                     tipo="Smart TV", svc=_MSheets(f))
    assert dest == "mestre-nova" and ok


@pytest.fixture(autouse=True)
def _isolado(monkeypatch):
    LA.limpa_cache_mestre()
    monkeypatch.setattr(LF, "_service", lambda: _MSheets(_fake_mestre()))
    yield
    LA.limpa_cache_mestre()
