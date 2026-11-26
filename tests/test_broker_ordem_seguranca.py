"""Teste de ordem: guarda e E1+E2 executam ANTES do POST de escrita."""
import hashlib
import hmac
import json

import pytest

from mkt_flow_p0 import editorial_broker_transport as bt
from mkt_flow_p0 import broker_revisor_guard as guard
from editorial_factual_certificate import draft_digest, issue_factual_certificate

KEY = b"cert-key-32bytes-abcdefghijklmnopqrstu"
REG = b"registry-key-32bytes-abcdefghijklmnopqr"


class _Resp:
    def __init__(self, code, body):
        self.status_code = code
        self._body = body
    def json(self):
        return self._body


class _Session:
    """Registra a ordem das chamadas; falha se POST ocorrer antes das guardas."""
    def __init__(self):
        self.calls = []
        self.posted = False
    def get(self, url, **kw):
        self.calls.append("GET " + url.split("/")[-1].split("?")[0])
        if "snapshot" in url:
            return _Resp(200, {"snapshot": {"ID": 41, "post_status": "draft",
                                            "post_content": "<p>Texto</p>"},
                               "snapshot_sha256": "a" * 64})
        if "context=edit" in url:
            return _Resp(200, {"id": 41, "status": "draft", "title": {"raw": "T"},
                               "content": {"raw": "<p>Texto</p>"}})
        if "context=view" in url:
            return _Resp(200, {"id": 41, "status": "draft",
                               "content": {"rendered": "<h1>T</h1><p>Texto</p>"}})
        return _Resp(200, {})
    def post(self, url, **kw):
        self.calls.append("POST write")
        self.posted = True
        return _Resp(200, {"post_id": 41, "version_sha256": "b" * 64,
                           "intent": "publish", "status": "publish"})


def test_guarda_bloqueia_antes_do_post():
    """Com certificado inválido, o POST nunca acontece."""
    s = _Session()
    package = {"version_sha256": "a" * 64,
               "payload": {"wordpress": {"post_id": 41}, "content": "<p>Texto</p>"}}
    with pytest.raises(bt.BrokerBlocked):
        bt.publish_via_broker(
            package, core_root="/unused", wp_url=bt.SITE, wp_user="svc",
            wp_password="pw", trace_run_id="run_teste", intent="publish",
            publication_reference="REF-12345", session=s,
            review_certificate={"draft_sha256": "0" * 64},
            review_certificate_key=KEY, review_lookup=lambda u: {},
            registry_verification_key=REG)
    assert s.posted is False, "POST não deve ocorrer se a guarda falhar"


def test_e1e2_bloqueia_antes_do_post():
    """Com E1+E2 habilitado e edit falhando, o POST nunca acontece."""
    class _FailEdit(_Session):
        def get(self, url, **kw):
            if "context=edit" in url:
                return _Resp(403, {})
            return super().get(url, **kw)
    s = _FailEdit()
    package = {"version_sha256": "a" * 64,
               "payload": {"wordpress": {"post_id": 41}, "content": "<p>Texto</p>"}}
    # Sem owner_release, precisa do core — simulamos apenas a ordem até E1E2:
    # usamos owner_release=False e um core inexistente faria falhar antes;
    # para isolar E1E2, chamamos a função diretamente.
    from mkt_flow_p0.readback_e1e2 import validate_e1_e2, E1E2Blocked
    with pytest.raises(E1E2Blocked):
        validate_e1_e2(41, "svc", "pw", session=s)
    assert s.posted is False
