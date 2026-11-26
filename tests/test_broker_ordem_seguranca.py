"""Testes de ordem e fail-closed do broker após última rodada de correções."""
import hashlib

import pytest

from mkt_flow_p0 import editorial_broker_transport as bt
from mkt_flow_p0 import review_keys as keys
from mkt_flow_p0.editorial_transport import SITE


class _Resp:
    def __init__(self, code, body):
        self.status_code = code
        self._body = body
    def json(self):
        return self._body


class _Session:
    def __init__(self):
        self.calls = []
        self.posted = False
    def get(self, url, **kw):
        self.calls.append(url)
        if "context=edit" in url:
            return _Resp(200, {"id": 41, "status": "draft", "title": {"raw": "T"},
                               "content": {"raw": "<p>Texto</p>"}})
        if "context=view" in url:
            return _Resp(200, {"id": 41, "status": "draft",
                               "content": {"rendered": "<h1>T</h1><p>Texto</p>"}})
        return _Resp(200, {"snapshot": {"ID": 41, "post_status": "draft",
                                        "post_content": "<p>Texto</p>"},
                           "snapshot_sha256": "a" * 64})
    def post(self, url, **kw):
        self.calls.append("POST write")
        self.posted = True
        return _Resp(200, {"post_id": 41, "version_sha256": "b" * 64,
                           "intent": "publish", "status": "publish"})


def _package():
    return {"version_sha256": "a" * 64,
            "payload": {"wordpress": {"post_id": 41}, "content": "<p>Texto</p>"}}


def test_post_id_extraido_antes_da_guarda(monkeypatch):
    """Com destino autorizado, post_id ausente falha com WP_POST_ID_MISSING,
    não com NameError (bug corrigido)."""
    import mkt_flow_p0.wp_destination as wd
    monkeypatch.setattr(wd, "resolve", lambda op: wd.WpDestination(
        url=SITE, user="svc", password="pw", environment="", operation=op))
    monkeypatch.setattr(wd, "assert_writable", lambda dest, op: None)
    s = _Session()
    monkeypatch.setenv("CONEXO_EDITORIAL_GATE_KEY", "c" * 40)
    monkeypatch.setenv("CONEXO_REVIEW_REGISTRY_KEY", "r" * 40)
    bad = {"version_sha256": "a" * 64, "payload": {"wordpress": {}}}
    with pytest.raises(bt.BrokerBlocked) as exc:
        bt.publish_via_broker(
            bad, core_root="/unused", wp_url=SITE, wp_user="svc", wp_password="pw",
            trace_run_id="run", intent="publish", publication_reference="REF-12345",
            session=s, review_certificate={"draft_sha256": "0" * 64})
    assert "WP_POST_ID_MISSING" in str(exc.value)
    assert s.posted is False


def test_e1e2_obrigatorio_por_padrao():
    """E1/E2 executam por padrão (sem parâmetro desligado)."""
    import inspect
    sig = inspect.signature(bt.publish_via_broker)
    assert sig.parameters["validate_e1e2_enabled"].default is True


def test_e1e2_falha_bloqueia_post():
    """Falha em E1 não permite POST."""
    class _FailEdit(_Session):
        def get(self, url, **kw):
            if "context=edit" in url:
                return _Resp(403, {})
            return super().get(url, **kw)
    s = _FailEdit()
    with pytest.raises(bt.BrokerBlocked):
        bt.publish_via_broker(
            _package(), core_root="/unused", wp_url=SITE, wp_user="svc",
            wp_password="pw", trace_run_id="run", intent="publish",
            publication_reference="REF-12345", session=s)
    assert s.posted is False


def test_chaves_separadas_sem_expor(monkeypatch):
    monkeypatch.setenv("CONEXO_EDITORIAL_GATE_KEY", "c" * 40)
    monkeypatch.setenv("CONEXO_REVIEW_REGISTRY_KEY", "r" * 40)
    status = keys.keys_status()
    assert status["safe_for_publication"] is True
    assert "c" * 40 not in str(status) and "r" * 40 not in str(status)


def test_sem_certificado_guarda_nao_exige_chaves():
    """Fluxo legado (sem certificado) continua compatível."""
    s = _Session()
    # Falhará no core (inexistente), mas não por chaves de revisor
    with pytest.raises(Exception):
        bt.publish_via_broker(
            _package(), core_root="/unused", wp_url=SITE, wp_user="svc",
            wp_password="pw", trace_run_id="run", intent="publish",
            publication_reference="REF-12345", session=s)
    assert s.posted is False
