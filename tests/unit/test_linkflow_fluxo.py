"""
Teste do FLUXO /link sem PTB real: injeta modulos `telegram`/`telegram.ext`
falsos e exercita cmd_link + on_lk com updates falsos, do link ate a gravacao.
Prova o desenho sem memoria (o estado vem do callback_data e do texto).
pytest tests/unit/test_linkflow_fluxo.py -v
"""
import asyncio
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "admin"))

# ---------- PTB falso (so o que o linkflow usa) ----------
class _Botao:
    def __init__(self, texto, callback_data=None, url=None):
        self.text, self.callback_data, self.url = texto, callback_data, url


class _Markup:
    def __init__(self, inline_keyboard):
        self.inline_keyboard = inline_keyboard

    def todos_callbacks(self):
        return [b.callback_data for linha in self.inline_keyboard for b in linha]


tg = types.ModuleType("telegram")
tg._FAKE = True  # marca para outros testes saberem que este PTB e um stub
tg.InlineKeyboardButton = _Botao
tg.InlineKeyboardMarkup = _Markup
tg.Update = object
ext = types.ModuleType("telegram.ext")
ext._FAKE = True


class _Handler:
    def __init__(self, *a, **k):
        self.args, self.kwargs = a, k


class _CommandHandler(_Handler):
    """Igual ao PTB: guarda `commands` como atributo (frozenset)."""

    def __init__(self, commands, callback, **kw):
        super().__init__(callback, **kw)
        if isinstance(commands, (list, tuple, set, frozenset)):
            self.commands = frozenset(commands)
        else:
            self.commands = frozenset({commands})
        self.callback = callback


class _CallbackQueryHandler(_Handler):
    """Igual ao PTB: guarda `pattern` (string ou regex compilada)."""

    def __init__(self, callback, pattern=None, **kw):
        super().__init__(callback, **kw)
        self.pattern = pattern
        self.callback = callback


ext.Application = object
ext.CommandHandler = _CommandHandler
ext.CallbackQueryHandler = _CallbackQueryHandler
ext.ConversationHandler = _Handler
ext.MessageHandler = _Handler
ext.filters = object
ext.ContextTypes = types.SimpleNamespace(DEFAULT_TYPE=object)
sys.modules["telegram"] = tg
sys.modules["telegram.ext"] = ext
# reimporta o linkflow ligado AO STUB (se outro teste ja importou com o PTB real)
for _m in ("linkflow", "admin", "admin.bot"):
    sys.modules.pop(_m, None)

import linkflow as L  # noqa: E402

PLANILHA = {}


def _celula(produto, loja, svc=None):
    return PLANILHA.get((produto, loja), "")


def _grava(produto, loja, url, svc=None):
    PLANILHA[(produto, loja)] = url
    return (True, url)


# monkeypatch (fixture) para NAO vazar para os outros testes da suite
import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _planilha_falsa(monkeypatch):
    PLANILHA.clear()
    # allowlist = o usuario de teste (1); o caso negativo esta em teste dedicado
    monkeypatch.setenv("TELEGRAM_ALLOWED_IDS", "1")
    monkeypatch.setattr(L, "le_celula", _celula)
    monkeypatch.setattr(L, "grava_link", _grava)
    yield
    PLANILHA.clear()


# ---------- updates falsos ----------
class _Msg:
    def __init__(self, texto, data=None):
        self.text = texto
        self.date = data or datetime.now(timezone.utc)
        self.editados = []
        self.replies = []

    async def reply_text(self, texto, **kw):
        self.replies.append((texto, kw.get("reply_markup")))
        return self

    async def edit_message_text(self, texto, **kw):
        self.editados.append((texto, kw.get("reply_markup")))
        return self


class _Q:
    """CallbackQuery falso: edit_message_text delega para a mensagem (como o PTB)."""

    def __init__(self, data, msg):
        self.data = data
        self.message = msg
        self.respondidas = []

    async def answer(self, *a, **k):
        self.respondidas.append((a, k))

    async def edit_message_text(self, texto, **kw):
        return await self.message.edit_message_text(texto, **kw)


class _Update:
    def __init__(self, texto_msg, data_msg=None, user_id=1, chat_id=1):
        self.effective_user = types.SimpleNamespace(id=user_id)
        self.effective_chat = types.SimpleNamespace(id=chat_id)
        self.message = _Msg(texto_msg, data_msg)
        self.callback_query = None

    def como_toque(self, data, data_msg=None):
        # o botao pertence a mensagem do BOT (que carrega o link). Se ja houve
        # resposta, o texto editado mais recente e o conteudo atual dela.
        texto = self.message.text
        if self.message.editados:
            texto = self.message.editados[-1][0]
        elif self.message.replies:
            texto = self.message.replies[-1][0]
        msg = _Msg(texto, data_msg or self.message.date)
        self.callback_query = _Q(data, msg)
        return self


class _Ctx:
    def __init__(self, args):
        self.args = args


def roda(coro):
    return asyncio.run(coro)


def test_fluxo_completo_grava_na_celula_certa():
    PLANILHA.clear()
    up = _Update("")
    roda(L.cmd_link(up, _Ctx(["https://link.amazon/B05GmEKKZ"])))
    texto, kb = up.message.replies[0]
    assert "Qual guia?" in texto and "https://link.amazon/B05GmEKKZ" in texto
    assert "lk:g:caixa_som" in kb.todos_callbacks()

    # 1) escolhe o guia
    up.como_toque("lk:g:caixa_som")
    roda(L.on_lk(up, _Ctx([])))
    texto2, kb2 = up.callback_query.message.editados[0]
    assert "Caixa de som" in texto2
    assert "lk:p:caixa_som:1" in kb2.todos_callbacks()

    # 2) escolhe o produto (indice 1 = Stormbox Blast 2)
    up.como_toque("lk:p:caixa_som:1")
    roda(L.on_lk(up, _Ctx([])))
    texto3, kb3 = up.callback_query.message.editados[0]
    assert "Stormbox Blast 2" in texto3
    assert "lk:l:caixa_som:1:3" in kb3.todos_callbacks()   # 3 = Amazon

    # 3) escolhe a loja -> grava
    up.como_toque("lk:l:caixa_som:1:3")
    roda(L.on_lk(up, _Ctx([])))
    texto4, _kb4 = up.callback_query.message.editados[0]
    assert "✅ Gravado" in texto4
    assert PLANILHA[("Tribit Stormbox Blast 2", "Amazon")] == "https://link.amazon/B05GmEKKZ"


def test_celula_ocupada_pergunta_antes_de_trocar():
    PLANILHA.clear()
    PLANILHA[("Tribit Stormbox Blast 2", "Amazon")] = "https://antigo.com/x"
    up = _Update("🔗 https://novo.com/y\nQual guia?")
    up.como_toque("lk:l:caixa_som:1:3")
    roda(L.on_lk(up, _Ctx([])))
    texto, kb = up.callback_query.message.editados[0]
    assert "Já existe link" in texto and "https://antigo.com/x" in texto
    assert "lk:x:caixa_som:1:3:1" in kb.todos_callbacks()
    # nada foi trocado ainda
    assert PLANILHA[("Tribit Stormbox Blast 2", "Amazon")] == "https://antigo.com/x"
    # "manter" nao muda
    up.como_toque("lk:x:caixa_som:1:3:0")
    roda(L.on_lk(up, _Ctx([])))
    assert PLANILHA[("Tribit Stormbox Blast 2", "Amazon")] == "https://antigo.com/x"
    # "trocar" grava o novo
    up.como_toque("lk:x:caixa_som:1:3:1")
    roda(L.on_lk(up, _Ctx([])))
    assert PLANILHA[("Tribit Stormbox Blast 2", "Amazon")] == "https://novo.com/y"


def test_botao_sem_link_avisa():
    up = _Update("Qual guia?")
    up.como_toque("lk:g:tv4k")
    roda(L.on_lk(up, _Ctx([])))
    texto, _ = up.callback_query.message.editados[0]
    assert "Não encontrei o link" in texto


def test_botao_antigo_de_24h_avisa():
    velho = datetime.now(timezone.utc) - timedelta(hours=30)
    up = _Update("🔗 https://a.com/x\nQual guia?", data_msg=velho)
    up.como_toque("lk:g:tv4k", data_msg=velho)
    roda(L.on_lk(up, _Ctx([])))
    texto, _ = up.callback_query.message.editados[0]
    assert "⏳" in texto


def test_callback_data_curto_para_o_telegram():
    """Telegram limita callback_data a 64 bytes."""
    up = _Update("")
    roda(L.cmd_link(up, _Ctx(["https://shopee.com.br/produto/123456789/abcdef"])))
    _texto, kb = up.message.replies[0]
    for cb in kb.todos_callbacks():
        assert len(cb.encode()) <= 64, cb
    up.como_toque("lk:g:caixa_som")
    roda(L.on_lk(up, _Ctx([])))
    _t, kb2 = up.callback_query.message.editados[0]
    for cb in kb2.todos_callbacks():
        assert len(cb.encode()) <= 64, cb
    up.como_toque("lk:p:caixa_som:1")
    roda(L.on_lk(up, _Ctx([])))
    _t3, kb3 = up.callback_query.message.editados[0]
    for cb in kb3.todos_callbacks():
        assert len(cb.encode()) <= 64, cb
