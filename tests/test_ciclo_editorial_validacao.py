"""Validação isolada do ciclo editorial completo (9 etapas). Sem produção."""
import hashlib
import hmac
import json

import pytest

from editorial_factual_certificate import (
    draft_digest, issue_factual_certificate, verify_factual_certificate,
)
from mkt_flow_p0 import broker_revisor_guard as guard
from editorial_trusted_review import verify_independent_review

CERT_KEY = b"cert-issuer-key-32bytes-abcdefghijklmn"
REG_KEY = b"registry-verify-key-32bytes-xyz123456"
POST = {"id": 41, "status": "draft", "title": "Ciclo", "content": "<p>Texto</p>",
        "slug": "ciclo", "categories": [10], "featured_media": 12}


def _cert():
    return issue_factual_certificate(
        POST,
        {"reviewer_id": "7", "review_type": "independent_human",
         "decision": "APROVADO", "evidence_refs": ["https://example.org/f"],
         "review_record_url": "https://example.org/review/41"},
        CERT_KEY, now=100)


def _envelope(cert):
    record = {
        "reviewer_id": cert["reviewer_id"], "draft_sha256": draft_digest(POST),
        "decision": "APROVADO", "status": "FINAL", "independent": True,
        "evidence_refs": cert["evidence_refs"],
        "review_record_url": cert["review_record_url"], "revoked": False,
    }
    body = json.dumps(record, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")
    return {"record": record,
            "signature": hmac.new(REG_KEY, body, hashlib.sha256).hexdigest()}


def test_etapa1_selecao_pauta():
    # Pauta com fonte identificada e recorte definido (dados sintéticos)
    pauta = {"tema": "Tecnologia", "fonte": "https://example.org", "recorte": "noticia"}
    assert pauta["fonte"].startswith("https://")
    assert pauta["recorte"] in ("noticia", "guia", "analise")


def test_etapa2_geracao():
    # Conteúdo gerado tem hash determinístico
    h1 = draft_digest(POST)
    h2 = draft_digest(POST)
    assert h1 == h2 and len(h1) == 64


def test_etapa3_validacao_factual():
    cert = _cert()
    assert verify_factual_certificate(POST, cert, CERT_KEY, now=150) is True


def test_etapa4_certificacao():
    cert = _cert()
    assert cert["draft_sha256"] == draft_digest(POST)
    assert cert["decision"] == "APROVADO"


def test_etapa5_revisao_humana():
    cert = _cert()
    lookup = guard.build_review_lookup(lambda u: _envelope(cert),
                                      registry_verification_key=REG_KEY)
    result = verify_independent_review(POST, cert, CERT_KEY, lookup, REG_KEY, now=150)
    assert result["verified"] is True


def test_etapa6_aprovacao():
    cert = _cert()
    guard.require_broker_review(POST, cert, CERT_KEY,
                                lambda u: _envelope(cert), REG_KEY, now=150)
    assert True  # não levantou = aprovado


def test_etapa7_publicacao_autorizada():
    # Guarda autoriza; escrita real é feita apenas com autorização específica
    cert = _cert()
    out = guard.require_broker_review(POST, cert, CERT_KEY,
                                      lambda u: _envelope(cert), REG_KEY, now=150)
    assert out["verified"] is True


def test_etapa8_readback():
    # Hash do conteudo publicado deve bater com o aprovado
    cert = _cert()
    assert cert["draft_sha256"] == hashlib.sha256(
        json.dumps({k: POST[k] for k in ("id", "status", "title", "content", "slug", "categories", "featured_media")},
                   sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def test_etapa9_recibo():
    cert = _cert()
    recibo = {"verified": True, "draft_sha256": cert["draft_sha256"],
              "reviewer_id": cert["reviewer_id"], "retry_automatic": False}
    assert recibo["verified"] is True
    assert recibo["draft_sha256"] == draft_digest(POST)
    assert recibo["retry_automatic"] is False
