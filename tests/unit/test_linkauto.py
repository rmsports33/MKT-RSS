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

PTB = LA._TEM_PTB

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
    monkeypatch.setenv("TELEGRAM_ALLOWED_IDS", "1")
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
    monkeypatch.setenv("TELEGRAM_ALLOWED_IDS", "1")
    monkeypatch.setattr(LF, "_service", lambda: _MSheets(_fake_mestre()))
    yield
    LA.limpa_cache_mestre()


# ---------------------------------------------------------------- handlers (PTB real)
precisa_ptb = pytest.mark.skipif(not PTB, reason="sem PTB aqui")


class _M:
    def __init__(self, texto, data=None, reply_to=None):
        self.text = texto
        self.date = data or datetime.now(timezone.utc)
        self.reply_to_message = reply_to
        self.edits = []
        self.replies = []

    async def reply_text(self, texto, **kw):
        self.replies.append((texto, kw.get("reply_markup")))
        return self

    async def edit_message_text(self, texto, **kw):
        self.edits.append((texto, kw.get("reply_markup")))
        return self


class _Q:
    def __init__(self, data, msg):
        self.data = data
        self.message = msg

    async def answer(self, *a, **k):
        pass

    async def edit_message_text(self, texto, **kw):
        return await self.message.edit_message_text(texto, **kw)


class _U:
    def __init__(self, msg=None, uid=1):
        self.message = msg
        self.effective_user = SimpleNamespace(id=uid)
        self.effective_chat = SimpleNamespace(id=1)
        self.callback_query = None

    def toque(self, data):
        base = self.message.text
        if self.message.edits:
            base = self.message.edits[-1][0]
        elif self.message.replies:
            base = self.message.replies[-1][0]
        self.callback_query = _Q(data, _M(base))
        return self


class _Ctx:
    def __init__(self, args):
        self.args = args


def _roda(coro):
    return asyncio.run(coro)


def _fake_get(html, final=None, status=200):
    def get(url, headers=None, timeout=None, allow_redirects=None):
        return SimpleNamespace(text=html, url=final or url, status_code=status)
    return get


@precisa_ptb
def test_cmd_link_detecta_e_confirma(monkeypatch):
    monkeypatch.setattr("requests.get", _fake_get(
        '<meta property="og:title" content="Tribit StormBox Blast 2 90W" />',
        "https://www.amazon.com.br/dp/X"))
    up = _U(_M(""))
    _roda(LA.cmd_link2(up, _Ctx(["https://link.amazon/ABC"])))
    texto, kb = up.message.replies[0]
    assert "Tribit Stormbox Blast 2" in texto and "Amazon" in texto
    cbs = [b.callback_data for l in kb.inline_keyboard for b in l]
    assert "lk:ok:" in cbs and all(len(c.encode()) <= 64 for c in cbs)


@precisa_ptb
def test_cmd_link_sem_titulo_mostra_guias(monkeypatch):
    monkeypatch.setattr("requests.get", _fake_get("<html></html>"))
    up = _U(_M(""))
    _roda(LA.cmd_link2(up, _Ctx(["https://lojaqualquer.com/x"])))
    texto, kb = up.message.replies[0]
    assert "Não reconheci" in texto
    cbs = [b.callback_data for l in kb.inline_keyboard for b in l]
    assert "lk:g:tv4k" in cbs and "lk:b:" in cbs and "lk:o:" in cbs


@precisa_ptb
def test_ok_grava_na_aba_quando_e_guia(monkeypatch):
    chamadas = []
    monkeypatch.setattr(LF, "grava_link",
                        lambda p, l, u: chamadas.append((p, l, u)) or (True, u))
    up = _U(_M("🔗 https://link.amazon/B05GmEKKZ\n📦 Tribit Stormbox Blast 2\n🏪 Amazon"))
    up.toque("lk:ok:")
    _roda(LA.on_auto(up, _Ctx([])))
    texto, _kb = up.callback_query.message.edits[0]
    assert "aba dos guias" in texto
    assert chamadas == [("Tribit Stormbox Blast 2", "Amazon", "https://link.amazon/B05GmEKKZ")]


@precisa_ptb
def test_buscar_tipo_produto_loja_grava_mestre(monkeypatch):
    f = _fake_mestre()
    monkeypatch.setattr(LF, "_service", lambda: _MSheets(f))
    up = _U(_M("🔗 https://x.com/a"))
    up.toque("lk:b:")
    _roda(LA.on_auto(up, _Ctx([])))
    t1, kb1 = up.callback_query.message.edits[0]
    assert "Qual tipo?" in t1
    ti = [b.callback_data for l in kb1.inline_keyboard for b in l].index("lk:bt:1")
    up.toque("lk:bt:1")  # Smart TV (ordenado: Celular=0, Smart TV=1)
    _roda(LA.on_auto(up, _Ctx([])))
    t2, kb2 = up.callback_query.message.edits[0]
    assert "Smart TV" in t2
    up.toque("lk:bp:1:1")  # Crystal U8600F
    _roda(LA.on_auto(up, _Ctx([])))
    t3, kb3 = up.callback_query.message.edits[0]
    assert "Crystal U8600F" in t3 and "Qual loja?" in t3
    up.toque("lk:bl:1:1:3")  # Amazon
    _roda(LA.on_auto(up, _Ctx([])))
    t4, _kb4 = up.callback_query.message.edits[0]
    assert "planilha mestre" in t4 and f["e"][4] == "https://x.com/a"


@precisa_ptb
def test_resposta_com_nome_desconhecido_pede_tipo_e_cria(monkeypatch):
    f = _fake_mestre()
    monkeypatch.setattr(LF, "_service", lambda: _MSheets(f))
    origem = _M("🔗 https://www.amazon.com.br/dp/X\n🏪 Amazon")
    up = _U(_M("Samsung U8000H 50", reply_to=origem))
    _roda(LA.on_resposta(up, _Ctx([])))
    t1, kb1 = up.message.replies[0]
    assert "Criar novo?" in t1 and "Samsung U8000H 50" in t1
    up2 = _U(_M(t1))
    up2.toque("lk:t:1")  # Smart TV
    _roda(LA.on_auto(up2, _Ctx([])))
    t2, _kb2 = up2.callback_query.message.edits[0]
    assert "revisar" in t2
    assert f["appends"][-1][:5] == ["Smart TV", "Samsung U8000H 50", "", "Amazon",
                                    "https://www.amazon.com.br/dp/X"]


@precisa_ptb
def test_resposta_sem_loja_detectada_pede_loja_antes(monkeypatch):
    f = _fake_mestre()
    monkeypatch.setattr(LF, "_service", lambda: _MSheets(f))
    origem = _M("🔗 https://x.com/u8000")
    up = _U(_M("Samsung U8000H 50", reply_to=origem))
    _roda(LA.on_resposta(up, _Ctx([])))
    t1, kb1 = up.message.replies[0]
    assert "Qual loja?" in t1
    assert "lk:tl:3" in [b.callback_data for l in kb1.inline_keyboard for b in l]
    up2 = _U(_M(t1))
    up2.toque("lk:tl:3")  # Amazon
    _roda(LA.on_auto(up2, _Ctx([])))
    t2, kb2 = up2.callback_query.message.edits[0]
    assert "Criar novo?" in t2 and "🏪 Amazon" in t2
    up3 = _U(_M(t2))
    up3.toque("lk:t:1")  # Smart TV
    _roda(LA.on_auto(up3, _Ctx([])))
    t3, _kb3 = up3.callback_query.message.edits[0]
    assert "revisar" in t3
    assert f["appends"][-1][:5] == ["Smart TV", "Samsung U8000H 50", "", "Amazon",
                                    "https://x.com/u8000"]


@precisa_ptb
def test_callbacks_novos_cabem_em_64_bytes(monkeypatch):
    f = _fake_mestre()
    monkeypatch.setattr(LF, "_service", lambda: _MSheets(f))
    cbs = []
    up = _U(_M("🔗 https://x.com/a"))
    up.toque("lk:b:")
    _roda(LA.on_auto(up, _Ctx([])))
    _t, kb = up.callback_query.message.edits[0]
    cbs += [b.callback_data for l in kb.inline_keyboard for b in l]
    up.toque("lk:bt:1")
    _roda(LA.on_auto(up, _Ctx([])))
    _t2, kb2 = up.callback_query.message.edits[0]
    cbs += [b.callback_data for l in kb2.inline_keyboard for b in l]
    up.toque("lk:bp:1:0")
    _roda(LA.on_auto(up, _Ctx([])))
    _t3, kb3 = up.callback_query.message.edits[0]
    cbs += [b.callback_data for l in kb3.inline_keyboard for b in l]
    assert cbs, "nenhum callback gerado"
    assert all(len(c.encode()) <= 64 for c in cbs), [c for c in cbs if len(c.encode()) > 64]
