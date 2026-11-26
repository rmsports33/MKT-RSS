"""Testes da guarda do Revisor Único integrada ao broker. Offline, sem rede."""
import hashlib
import hmac
import json

import pytest

from mkt_flow_p0 import broker_revisor_guard as g
from editorial_factual_certificate import (
    draft_digest, issue_factual_certificate,
)

CERT_KEY = b"certificate-issuer-key-32bytes-abcdefgh"
REG_KEY = b"registry-verification-key-32bytes-xyz123"


def _post():
    return {"id": 41, "status": "draft", "title": "Teste", "content": "<p>Texto</p>",
            "slug": "teste", "categories": [10], "featured_media": 12}


def _cert(post):
    record = {
        "reviewer_id": "7", "review_type": "independent_human",
        "decision": "APROVADO", "evidence_refs": ["https://example.org/fonte"],
        "review_record_url": "https://example.org/review/41",
    }
    return issue_factual_certificate(post, record, CERT_KEY, now=100)


def _envelope(record):
    body = json.dumps(record, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")
    return {"record": record,
            "signature": hmac.new(REG_KEY, body, hashlib.sha256).hexdigest()}


def _record(post, cert):
    return {
        "reviewer_id": cert["reviewer_id"],
        "draft_sha256": draft_digest(post),
        "decision": "APROVADO", "status": "FINAL", "independent": True,
        "evidence_refs": cert["evidence_refs"],
        "review_record_url": cert["review_record_url"], "revoked": False,
    }


def test_guard_aprovada():
    post, cert = _post(), None
    cert = _cert(post)
    adapter = lambda url: _envelope(_record(post, cert))
    out = g.require_broker_review(post, cert, CERT_KEY, adapter, REG_KEY, now=150)
    assert out["verified"] is True


def test_envelope_sem_assinatura_bloqueia():
    post = _post()
    cert = _cert(post)
    record = _record(post, cert)
    adapter = lambda url: {"record": record}
    with pytest.raises(g.BrokerReviewBlocked):
        g.require_broker_review(post, cert, CERT_KEY, adapter, REG_KEY, now=150)


def test_envelope_adulterado_bloqueia():
    post = _post()
    cert = _cert(post)
    rec = _record(post, cert)
    rec["decision"] = "REPROVADO"
    env = _envelope(rec)
    env["record"] = dict(rec, decision="APROVADO")  # adultera sem reassinar
    with pytest.raises(g.BrokerReviewBlocked):
        g.require_broker_review(post, cert, CERT_KEY, lambda u: env, REG_KEY, now=150)


def test_chave_registry_errada_bloqueia():
    post = _post()
    cert = _cert(post)
    adapter = lambda url: _envelope(_record(post, cert))
    with pytest.raises(g.BrokerReviewBlocked):
        g.require_broker_review(post, cert, CERT_KEY, adapter,
                                b"wrong-key-32bytes-abcdefghijklmnop", now=150)


def test_revisor_divergente_bloqueia():
    post = _post()
    cert = _cert(post)
    rec = _record(post, cert)
    rec["reviewer_id"] = "999"
    with pytest.raises(g.BrokerReviewBlocked):
        g.require_broker_review(post, cert, CERT_KEY, lambda u: _envelope(rec), REG_KEY, now=150)


def test_certificado_invalido_bloqueia():
    post = _post()
    cert = _cert(post)
    cert["signature"] = "0" * 64
    with pytest.raises(g.BrokerReviewBlocked):
        g.require_broker_review(post, cert, CERT_KEY,
                                lambda u: _envelope(_record(post, cert)), REG_KEY, now=150)


def test_adapter_indisponivel_bloqueia():
    post = _post()
    cert = _cert(post)
    def boom(url):
        raise TimeoutError("timeout")
    with pytest.raises(g.BrokerReviewBlocked):
        g.require_broker_review(post, cert, CERT_KEY, boom, REG_KEY, now=150)


def test_sem_chave_de_verificacao_bloqueia():
    post = _post()
    cert = _cert(post)
    with pytest.raises(g.BrokerReviewBlocked):
        g.build_review_lookup(lambda u: {}, registry_verification_key=b"short")
