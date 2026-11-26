"""Testes do adaptador real, chaves separadas e E1+E2. Offline, sem rede real."""
import hashlib
import json

import pytest

from mkt_flow_p0 import registry_adapter_real as reg
from mkt_flow_p0 import review_keys as keys
from mkt_flow_p0 import readback_e1e2 as e12
from mkt_flow_p0.editorial_transport import SITE

HOST = SITE.rstrip("/") + "/review/41"


class _Resp:
    def __init__(self, code, body):
        self.status_code = code
        self._body = body
    def json(self):
        return self._body


class _Session:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []
    def get(self, url, **kw):
        self.calls.append(url)
        key = "edit" if "context=edit" in url else ("view" if "context=view" in url else "registry")
        return self.responses[key]


def test_chaves_status_sem_expor_valores(monkeypatch):
    monkeypatch.setenv("CONEXO_EDITORIAL_GATE_KEY", "c" * 40)
    monkeypatch.setenv("CONEXO_REVIEW_REGISTRY_KEY", "r" * 40)
    out = keys.keys_status()
    assert out["certificate_key_available"] is True
    assert out["registry_key_available"] is True
    assert out["keys_are_distinct"] is True
    assert out["safe_for_publication"] is True
    assert "c" * 40 not in str(out) and "r" * 40 not in str(out)


def test_chaves_iguais_bloqueiam(monkeypatch):
    monkeypatch.setenv("CONEXO_EDITORIAL_GATE_KEY", "x" * 40)
    monkeypatch.setenv("CONEXO_REVIEW_REGISTRY_KEY", "x" * 40)
    assert keys.keys_status()["safe_for_publication"] is False


def test_adaptador_real_retorna_envelope():
    env = {"record": {"reviewer_id": "7"}, "signature": "a" * 64}
    s = _Session({"registry": _Resp(200, env)})
    adapter = reg.build_registry_adapter(wp_user="svc", wp_app_password="pw", session=s)
    assert adapter(HOST) == env


def test_adaptador_rejeita_host_fora_do_destino():
    s = _Session({"registry": _Resp(200, {})})
    adapter = reg.build_registry_adapter(wp_user="svc", wp_app_password="pw", session=s)
    with pytest.raises(reg.RegistryAdapterBlocked):
        adapter("https://outro-dominio.example/review/1")


def test_e1e2_correlacionado():
    raw = "<p>Texto do artigo</p>"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    s = _Session({
        "edit": _Resp(200, {"id": 41, "status": "draft",
                             "title": {"raw": "Titulo"},
                             "content": {"raw": raw}}),
        "view": _Resp(200, {"id": 41, "status": "draft",
                             "content": {"rendered": raw}}),
    })
    out = e12.validate_e1_e2(41, "svc", "pw", session=s, expected_sha256=digest)
    assert out["verified"] is True
    assert out["content_sha256"] == digest
    assert out["e1e2_correlated"] is True
    assert len(s.calls) == 2  # E1 e E2 antes da escrita


def test_e1e2_sem_hash_esperado_bloqueia():
    raw = "<p>Texto</p>"
    s = _Session({
        "edit": _Resp(200, {"id": 41, "status": "draft", "title": {"raw": "T"},
                             "content": {"raw": raw}}),
        "view": _Resp(200, {"id": 41, "status": "draft",
                             "content": {"rendered": "<h1>T</h1>" + raw}}),
    })
    with pytest.raises(e12.E1E2Blocked) as exc:
        e12.validate_e1_e2(41, "svc", "pw", session=s, expected_sha256=None)
    assert "E1_EXPECTED_HASH_REQUIRED" in str(exc.value)


def test_e1e2_renderizado_divergente_bloqueia():
    """Renderizado com texto diferente do bruto deve bloquear."""
    raw = "<p>Texto original aprovado</p>"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    s = _Session({
        "edit": _Resp(200, {"id": 41, "status": "draft", "title": {"raw": "T"},
                             "content": {"raw": raw}}),
        "view": _Resp(200, {"id": 41, "status": "draft",
                             "content": {"rendered": "<p>Texto alterado sem autorizacao</p>"}}),
    })
    with pytest.raises(e12.E1E2Blocked) as exc:
        e12.validate_e1_e2(41, "svc", "pw", session=s, expected_sha256=digest)
    assert "E1E2_RENDERED_CONTENT_MISMATCH" in str(exc.value)


def test_e1e2_status_divergente_bloqueia():
    raw = "<p>Texto</p>"
    s = _Session({
        "edit": _Resp(200, {"id": 41, "status": "draft", "title": {"raw": "T"},
                             "content": {"raw": raw}}),
        "view": _Resp(200, {"id": 41, "status": "publish",
                             "content": {"rendered": "T" + raw}}),
    })
    with pytest.raises(e12.E1E2Blocked):
        e12.validate_e1_e2(41, "svc", "pw", session=s)


def test_e1e2_hash_divergente_bloqueia():
    raw = "<p>Texto</p>"
    s = _Session({
        "edit": _Resp(200, {"id": 41, "status": "draft", "title": {"raw": "T"},
                             "content": {"raw": raw}}),
        "view": _Resp(200, {"id": 41, "status": "draft",
                             "content": {"rendered": "T" + raw}}),
    })
    with pytest.raises(e12.E1E2Blocked):
        e12.validate_e1_e2(41, "svc", "pw", session=s, expected_sha256="0" * 64)
