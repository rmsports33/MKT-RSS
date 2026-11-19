"""Fase B — fronteira protegida v2.3: nenhum HMAC ou `alg` ausente é aceito.

Os testes legados continuam usando o caminho HMAC isolado; aqui o caminho
protegido é explícito (`require_contract_v23=True`). Sem broker, WordPress,
Gate PHP, produção, merge ou deploy.
"""
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from editorial_factual_certificate import (
    draft_digest,
    sign_factual_certificate,
)
from editorial_publish_gate import authorize_publish
from editorial_review_registry import InMemorySequenceStore, sign_registry_envelope
from editorial_trusted_review import (
    sign_registry_record,
    verify_independent_review_contract,
)

NOW = 150
URL = "https://example.org/reviews/fronteira-42"
POST = {
    "id": 42, "status": "draft", "title": {"raw": "Notícia verificada"},
    "content": {"raw": "<p>Corpo com fonte atribuída e conclusão verificável.</p>"},
    "slug": "noticia-verificada", "categories": [10], "featured_media": 456,
    "link": "https://conexotech.com.br/?p=42",
}


def _keys():
    issuer = Ed25519PrivateKey.generate()
    registry = Ed25519PrivateKey.generate()
    return issuer, issuer.public_key(), registry, registry.public_key()


def _body(**overrides):
    body = {
        "version": 1, "review_type": "independent_human",
        "draft_sha256": draft_digest(POST), "decision": "APROVADO",
        "reviewer_id": "revisor-unico-3", "review_record_url": URL,
        "evidence_refs": ["https://example.org/fonte"],
        "issued_at": 100, "expires_at": 200,
    }
    body.update(overrides)
    return body


def _record(**overrides):
    record = {
        "reviewer_id": "revisor-unico-3", "review_record_url": URL,
        "draft_sha256": draft_digest(POST), "decision": "APROVADO",
        "status": "FINAL", "independent": True, "revoked": False,
        "evidence_refs": ["https://example.org/fonte"],
        "issued_at": 100, "expires_at": 200,
    }
    record.update(overrides)
    return record


def _envelope(registry):
    return sign_registry_envelope(_record(), served_at=NOW, registry_seq=3,
                                  private_key=registry, kid="reg-2026-11")


def _strict(cert, envelope, issuer_pub, registry_pub):
    return verify_independent_review_contract(
        POST, cert, issuer_pub, lambda _: envelope, registry_pub,
        now=NOW, sequence_store=InMemorySequenceStore())


def test_contract_rejects_certificate_without_alg():
    _, issuer_pub, registry, registry_pub = _keys()
    cert = dict(_body())
    assert _strict(cert, _envelope(registry), issuer_pub, registry_pub)["reason"] == (
        "certificate_algorithm_missing")


def test_contract_rejects_legacy_hmac_certificate_alg():
    _, issuer_pub, registry, registry_pub = _keys()
    cert = {**_body(), "alg": "HMAC-SHA256"}
    assert _strict(cert, _envelope(registry), issuer_pub, registry_pub)["reason"] == (
        "certificate_algorithm_legacy_hmac")


def test_contract_rejects_unknown_certificate_alg():
    _, issuer_pub, registry, registry_pub = _keys()
    cert = {**_body(), "alg": "alg/custom"}
    assert _strict(cert, _envelope(registry), issuer_pub, registry_pub)["reason"] == (
        "certificate_algorithm_unsupported")


def test_contract_rejects_envelope_without_alg_downgrade():
    issuer, issuer_pub, _, registry_pub = _keys()
    cert = sign_factual_certificate(_body(), issuer, kid="iss-2026-11")
    legacy = {"record": _record(), "signature": sign_registry_record(_record(), b"x" * 32)}
    assert _strict(cert, legacy, issuer_pub, registry_pub)["reason"] == (
        "review_record_algorithm_missing")


def test_contract_rejects_envelope_with_hmac_alg():
    issuer, issuer_pub, _, registry_pub = _keys()
    cert = sign_factual_certificate(_body(), issuer, kid="iss-2026-11")
    envelope = {**_envelope(Ed25519PrivateKey.generate()), "alg": "HMAC-SHA256"}
    assert _strict(cert, envelope, issuer_pub, registry_pub)["reason"] == (
        "review_record_algorithm_legacy_hmac")


def test_contract_rejects_envelope_with_unknown_alg():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(_body(), issuer, kid="iss-2026-11")
    envelope = {**_envelope(registry), "alg": "RSA-PSS"}
    assert _strict(cert, envelope, issuer_pub, registry_pub)["reason"] == (
        "review_record_algorithm_unsupported")


def test_contract_accepts_only_the_full_ed25519_chain():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(_body(), issuer, kid="iss-2026-11")
    assert _strict(cert, _envelope(registry), issuer_pub, registry_pub)[
        "verified"] is True


def test_gate_contract_mode_blocks_legacy_certificate():
    _, _, registry, _ = _keys()
    legacy_cert = dict(_body())
    result = authorize_publish(
        POST, {}, now=NOW, require_contract_v23=True,
        review_certificate=legacy_cert, review_signing_key=b"x" * 32,
        registry_verification_key=b"y" * 32,
        lookup_review=lambda _: _envelope(registry))
    assert "trusted_factual_review_certificate_algorithm_missing" in result["bloqueios"]
    assert result["autorizado"] is False


def test_gate_contract_mode_blocks_legacy_envelope():
    issuer, issuer_pub, _, registry_pub = _keys()
    cert = sign_factual_certificate(_body(), issuer, kid="iss-2026-11")
    legacy = {"record": _record(), "signature": sign_registry_record(_record(), b"x" * 32)}
    result = authorize_publish(
        POST, {}, now=NOW, require_contract_v23=True,
        review_certificate=cert, review_signing_key=issuer_pub,
        registry_verification_key=registry_pub,
        lookup_review=lambda _: legacy)
    assert "trusted_factual_review_review_record_algorithm_missing" in result["bloqueios"]
    assert result["autorizado"] is False


def test_gate_default_mode_preserves_isolated_legacy_tests():
    # Compatibilidade permanece no modo padrão; o modo protegido é explícito.
    import hashlib
    import hmac

    from editorial_factual_certificate import canonical_bytes

    key = b"x" * 32
    registry_key = b"y" * 32
    body = _body()
    cert = {**body,
            "signature": hmac.new(key, canonical_bytes(body), hashlib.sha256).hexdigest()}
    legacy = {"record": _record(),
              "signature": sign_registry_record(_record(), registry_key)}
    result = authorize_publish(
        POST, {}, now=NOW, review_certificate=cert, review_signing_key=key,
        registry_verification_key=registry_key,
        lookup_review=lambda _: legacy)
    review_blockers = [b for b in result["bloqueios"]
                       if b.startswith("trusted_factual_review_")]
    assert review_blockers == []
    assert result["autorizado"] is False
