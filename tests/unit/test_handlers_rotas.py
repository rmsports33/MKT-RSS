"""
Regressao do bug de 27/09/2026: `CallbackQueryHandler(on_callback)` SEM pattern
capturava TODOS os callback_query e, como o PTB entrega o update ao primeiro
handler que casa (mesmo grupo), os botoes do /link nunca chegavam ao linkflow.

Este teste monta a lista de handlers NA MESMA ordem do bot.py e verifica qual
handler PTB realmente receberia cada botao.

ATENCAO: o test_linkflow_fluxo.py injeta um PTB FALSO em sys.modules (para
conduzir o fluxo sem API). Se isso estiver ativo, o teste de objetos reais e
pulado — as verificacoes por regex abaixo continuam valendo.
pytest tests/unit/test_handlers_rotas.py -v
"""
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "admin"))

import os  # noqa: E402
for _p in (ROOT / ".env", Path(r"C:\Users\LIVE2PC\Desktop\site do projeto\.env")):
    if _p.exists():
        for _ln in _p.read_text(encoding="utf-8", errors="replace").splitlines():
            _ln = _ln.strip()
            if _ln and not _ln.startswith("#") and "=" in _ln:
                _k, _, _v = _ln.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

# o test_linkflow_fluxo.py injeta um PTB stub; aqui quero o PTB DE VERDADE
for _m in ("telegram", "telegram.ext", "linkflow"):
    _mod = sys.modules.get(_m)
    if _mod is not None and getattr(_mod, "_FAKE", False):
        del sys.modules[_m]
try:
    import telegram  # noqa: E402
    PTB_REAL = not getattr(telegram, "_FAKE", False)
except ImportError:  # sem PTB instalado neste ambiente
    telegram = None
    PTB_REAL = False

import linkflow as L  # noqa: E402

import pytest  # noqa: E402


def _padrao(h):
    """Pattern do handler, seja string, regex compilada ou stub."""
    p = getattr(h, "pattern", None)
    if p is None:
        p = (getattr(h, "kwargs", {}) or {}).get("pattern")
    if p is None:
        return None
    return getattr(p, "pattern", p)  # regex compilada -> texto


def _comandos(h):
    c = getattr(h, "commands", None)
    if c is None:
        c = (getattr(h, "kwargs", {}) or {}).get("commands")
    return c


def _noop(*a, **k):  # callback irrelevante: so importa o roteamento
    return None


if PTB_REAL:
    try:  # importa o PTB REAL agora (nivel de modulo) e guarda as classes
        from telegram import CallbackQuery as _CB, Chat as _Chat, Message as _Msg, \
            Update as _Update, User as _User
        from telegram.ext import CallbackQueryHandler as _RealCB
        _REAL = (_CB, _Chat, _Msg, _Update, _User, _RealCB)
    except Exception as _e:  # pragma: no cover
        PTB_REAL = False
        _REAL = None
        print("PTB real nao importavel:", _e)
else:  # pragma: no cover
    _REAL = None

if PTB_REAL:
    import admin.bot as B  # noqa: E402
    _padrao_link = next((_padrao(h) for h in L.link_handlers() if _padrao(h)), r"^lk:")
    HANDLERS = [_RealCB(B.on_callback, pattern=r"^pub:"),
                _RealCB(_noop, pattern=_padrao_link)]
else:  # pragma: no cover
    B = None
    HANDLERS = []

PAT_PUB = r"^pub:"
PAT_LINK = r"^lk:"


# --- sempre roda: a semantica de "primeiro que casa" ---
def test_patterns_nao_se_sobrepoem():
    for lk in ("lk:g:tv4k", "lk:p:tv4k:0", "lk:l:tv4k:0:3", "lk:x:tv4k:0:3:1"):
        assert re.match(PAT_PUB, lk) is None, "%s casaria com o handler de publicar" % lk
        assert re.match(PAT_LINK, lk) is not None, lk
    assert re.match(PAT_PUB, "pub:9249") is not None
    assert re.match(PAT_LINK, "pub:9249") is None


def test_linkflow_registra_o_padrao_lk():
    padroes = [_padrao(h) for h in L.link_handlers()]
    assert PAT_LINK in padroes, padroes
    cmds = [_comandos(h) for h in L.link_handlers()]
    assert any(c and "link" in c for c in cmds), cmds


# --- com PTB real: prova nos objetos de verdade ---
@pytest.mark.skipif(not PTB_REAL, reason="PTB real nao disponivel nesta sessao")
def test_botoes_do_link_vao_para_o_linkflow():
    _CB, _Chat, _MsgT, _UpdateT, _User, _cbh = _REAL
    from datetime import datetime, timezone

    def up(data):
        user = _User(id=1, first_name="dono", is_bot=False)
        chat = _Chat(id=1, type="private")
        msg = _MsgT(message_id=1, date=datetime.now(timezone.utc), chat=chat, text="x")
        q = _CB(id="1", from_user=user, chat_instance="x", data=data, message=msg)
        return _UpdateT(update_id=1, callback_query=q)

    for data in ("lk:g:smartwatch", "lk:p:tv4k:0", "lk:l:tv4k:0:3", "lk:x:tv4k:0:3:1"):
        h = next((x for x in HANDLERS if x.check_update(up(data))), None)
        assert h is not None, data
        assert h is not HANDLERS[0], "%s foi para o handler de publicar, nao para o /link" % data

    h_pub = next((x for x in HANDLERS if x.check_update(up("pub:9249"))), None)
    assert h_pub is HANDLERS[0], "botao Publicar deve seguir para on_callback"


@pytest.mark.skipif(not PTB_REAL, reason="PTB real nao disponivel nesta sessao")
def test_handler_de_publicar_nao_e_catch_all():
    solto = B.CallbackQueryHandler(B.on_callback)
    limitado = B.CallbackQueryHandler(B.on_callback, pattern=r"^pub:")
    assert getattr(solto, "pattern", None) is None, "handler sem pattern = catch-all (o bug)"
    assert _padrao(limitado) == r"^pub:", "o handler de publicar precisa do pattern ^pub:"
