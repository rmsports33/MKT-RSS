"""
Regressao do bug de 27/09/2026: `CallbackQueryHandler(on_callback)` SEM pattern
capturava TODOS os callback_query e, como o PTB entrega o update ao primeiro
handler que casa (mesmo grupo), os botoes do /link nunca chegavam ao linkflow.

Este teste monta a lista de handlers NA MESMA ordem do bot.py e verifica qual
handler PTB realmente receberia cada botao.
pytest tests/unit/test_handlers_rotas.py -v
"""
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

import admin.bot as B  # noqa: E402
import linkflow as L  # noqa: E402
from telegram.ext import CallbackQueryHandler  # noqa: E402

# mesma ordem do bot.main()
HANDLERS = ([CallbackQueryHandler(B.on_callback, pattern=r"^pub:")] if hasattr(B, "on_callback")
            else []) + L.link_handlers()


def _update_cb(data):
    """Update REAL do PTB (o check_update exige isinstance(Update))."""
    from telegram import CallbackQuery, Chat, Message, Update, User
    from datetime import datetime, timezone
    user = User(id=1, first_name="dono", is_bot=False)
    chat = Chat(id=1, type="private")
    msg = Message(message_id=1, date=datetime.now(timezone.utc), chat=chat, text="x")
    q = CallbackQuery(id="1", from_user=user, chat_instance="x", data=data, message=msg)
    return Update(update_id=1, callback_query=q)


def _primeiro_que_casa(data):
    for h in HANDLERS:
        if h.check_update(_update_cb(data)):
            return h
    return None


def test_botoes_do_link_vao_para_o_linkflow():
    for data in ("lk:g:smartwatch", "lk:g:tv4k", "lk:p:tv4k:0",
                 "lk:l:tv4k:0:3", "lk:x:tv4k:0:3:1"):
        h = _primeiro_que_casa(data)
        assert h is not None, data
        assert h is not HANDLERS[0], ("%s foi para o handler de publicar, nao para o /link" % data)


def test_publicar_continua_no_seu_handler():
    h = _primeiro_que_casa("pub:9249")
    assert h is HANDLERS[0], "botao Publicar deve seguir para on_callback"


def test_handler_de_publicar_nao_e_catch_all():
    """Sem pattern, o handler de publicar engoliria tudo — trava de regressao."""
    solto = CallbackQueryHandler(B.on_callback)
    assert solto.check_update(_update_cb("lk:g:tv4k")) is True, \
        "handler sem pattern deveria casar qualquer botao (era o bug)"
    limitado = CallbackQueryHandler(B.on_callback, pattern=r"^pub:")
    assert limitado.check_update(_update_cb("lk:g:tv4k")) is None, \
        "com pattern ^pub: o botao do /link NAO pode casar"


def test_command_link_registrado():
    cmds = [getattr(h, "commands", None) for h in HANDLERS]
    assert any(c and "link" in c for c in cmds), "faltou o CommandHandler('link')"
