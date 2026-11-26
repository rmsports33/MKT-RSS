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
        self.auths = []
        self.posted = False
    def get(self, url, **kw):
        self.calls.append(url)
        self.auths.append(kw.get("auth"))
        if "context=edit" in url:
            return _Resp(200, {"id": 41, "status": "draft", "title": {"raw": "Teste"},
                               "content": {"raw": "<p>Texto</p>"}, "slug": "teste",
                               "categories": [10], "featured_media": 12})
        if "context=view" in url:
            return _Resp(200, {"id": 41, "status": "draft",
                               "content": {"rendered": "<p>Texto</p>"}})
        return _Resp(200, {"snapshot": {"ID": 41,
                                        "post_status": "publish" if self.posted else "draft",
                                        "post_content": "<p>Texto</p>"},
                           "snapshot_sha256": "a" * 64})
    def post(self, url, **kw):
        self.calls.append("POST write")
        self.auths.append(kw.get("auth"))
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


def test_e1e2_obrigatorio_sem_parametro():
    """Não existe parâmetro para desativar E1/E2."""
    import inspect
    sig = inspect.signature(bt.publish_via_broker)
    assert "validate_e1e2_enabled" not in sig.parameters


def test_guarda_obrigatoria_sem_certificado(monkeypatch):
    """Mesmo com destino válido, ausência do certificado bloqueia sem GET/POST."""
    import mkt_flow_p0.wp_destination as wd
    monkeypatch.setattr(wd, "resolve", lambda op: wd.WpDestination(
        url=SITE, user="svc", password="pw", environment="", operation=op))
    monkeypatch.setattr(wd, "assert_writable", lambda dest, op: None)
    s = _Session()
    with pytest.raises(bt.BrokerBlocked, match="REVISOR_UNICO_CERTIFICATE_MISSING"):
        bt.publish_via_broker(
            _package(), core_root="/unused", wp_url=SITE, wp_user="svc",
            wp_password="pw", trace_run_id="run", intent="publish",
            publication_reference="REF-12345", session=s)
    assert s.posted is False
    assert s.calls == []


def test_e1e2_falha_bloqueia_post(monkeypatch):
    """Falha E1 depois das validações locais não permite POST."""
    import mkt_flow_p0.wp_destination as wd
    monkeypatch.setattr(wd, "resolve", lambda op: wd.WpDestination(
        url=SITE, user="svc", password="pw", environment="", operation=op))
    monkeypatch.setattr(wd, "assert_writable", lambda dest, op: None)
    monkeypatch.setenv("CONEXO_EDITORIAL_GATE_KEY", "c" * 40)
    monkeypatch.setenv("CONEXO_REVIEW_REGISTRY_KEY", "r" * 40)
    class _FailEdit(_Session):
        def get(self, url, **kw):
            if "context=edit" in url:
                self.calls.append(url)
                self.auths.append(kw.get("auth"))
                return _Resp(403, {})
            return super().get(url, **kw)
    class _Core:
        @staticmethod
        def validator():
            class _Validator:
                @staticmethod
                def evaluate(*args, **kwargs):
                    return [], []
            return _Validator()
    monkeypatch.setattr(bt, "load_core", lambda root: _Core)
    monkeypatch.setattr(bt, "require_release_trace", lambda package, run_id: None)
    package = _package()
    package["review_certificate"] = {"synthetic": True}
    s = _FailEdit()
    with pytest.raises(bt.BrokerBlocked, match="E1E2_READ_HTTP_REJECTED"):
        bt.publish_via_broker(
            package, core_root="/unused", wp_url=SITE, wp_user="svc",
            wp_password="pw", trace_run_id="run", intent="publish",
            publication_reference="REF-12345", session=s)
    assert s.posted is False
    assert "POST write" not in s.calls


def test_chaves_separadas_sem_expor(monkeypatch):
    monkeypatch.setenv("CONEXO_EDITORIAL_GATE_KEY", "c" * 40)
    monkeypatch.setenv("CONEXO_REVIEW_REGISTRY_KEY", "r" * 40)
    status = keys.keys_status()
    assert status["safe_for_publication"] is True
    assert "c" * 40 not in str(status) and "r" * 40 not in str(status)




def test_broker_rejeita_credenciais_divergentes_do_destino(monkeypatch):
    import mkt_flow_p0.wp_destination as wd
    monkeypatch.setattr(wd, "resolve", lambda op: wd.WpDestination(
        url=SITE, user="wp-validado", password="senha-validada",
        environment="", operation=op))
    monkeypatch.setattr(wd, "assert_writable", lambda dest, op: None)
    session = _Session()
    with pytest.raises(bt.BrokerBlocked, match="WP_DESTINATION_ARGUMENT_MISMATCH"):
        bt.publish_via_broker(
            _package(), core_root="/unused", wp_url=SITE, wp_user="wp-antigo",
            wp_password="senha-antiga", trace_run_id="run", intent="publish",
            publication_reference="REF-12345", session=session)
    assert session.calls == []
    assert session.posted is False


def test_broker_entrega_post_e_hash_de_conteudo_autenticados_ao_revisor(monkeypatch):
    import mkt_flow_p0.wp_destination as wd
    from mkt_flow_p0 import broker_revisor_guard as guard
    from mkt_flow_p0 import readback_e1e2 as e12

    monkeypatch.setattr(wd, "resolve", lambda op: wd.WpDestination(
        url=SITE, user="svc", password="pw", environment="", operation=op))
    monkeypatch.setattr(wd, "assert_writable", lambda dest, op: None)
    monkeypatch.setenv("CONEXO_EDITORIAL_GATE_KEY", "c" * 40)
    monkeypatch.setenv("CONEXO_REVIEW_REGISTRY_KEY", "r" * 40)

    observed = {}
    def fake_guard(post, certificate, certificate_key, lookup, registry_key):
        observed["post"] = post
        observed["certificate"] = certificate
        observed["certificate_key"] = certificate_key
        observed["registry_key"] = registry_key
        return {"verified": True}
    monkeypatch.setattr(guard, "require_broker_review", fake_guard)

    class _Core:
        @staticmethod
        def validator():
            class _Validator:
                @staticmethod
                def evaluate(*args, **kwargs):
                    return [], []
            return _Validator()
    monkeypatch.setattr(bt, "load_core", lambda root: _Core)
    monkeypatch.setattr(bt, "require_release_trace", lambda package, run_id: None)

    original = e12.validate_e1_e2
    def capture_e1e2(*args, **kwargs):
        observed["expected_e1_sha256"] = kwargs["expected_sha256"]
        return original(*args, **kwargs)
    monkeypatch.setattr(e12, "validate_e1_e2", capture_e1e2)

    package = _package()
    package["version_sha256"] = "b" * 64
    package["review_certificate"] = {"synthetic": True}
    session = _Session()
    result = bt.publish_via_broker(
        package, core_root="/unused", wp_url=SITE, wp_user="svc", wp_password="pw",
        trace_run_id="run", intent="publish", publication_reference="REF-12345",
        session=session)

    expected_content_hash = hashlib.sha256(b"<p>Texto</p>").hexdigest()
    assert result["verified"] is True
    assert observed["post"] == {
        "id": 41, "status": "draft", "title": {"raw": "Teste"},
        "content": {"raw": "<p>Texto</p>"}, "slug": "teste",
        "categories": [10], "featured_media": 12,
    }
    assert observed["expected_e1_sha256"] == expected_content_hash
    assert observed["expected_e1_sha256"] != "a" * 64
    assert observed["certificate"] == {"synthetic": True}
    assert observed["certificate_key"] != observed["registry_key"]
    assert session.posted is True
    assert all(auth == ("svc", "pw") for auth in session.auths)
