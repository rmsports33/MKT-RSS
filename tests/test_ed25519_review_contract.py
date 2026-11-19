"""Fase B OFFLINE — protocolo Ed25519 e fronteira autenticada do registro.

Cada nome de teste contém o ID SEC do contrato v2.3. Nenhum teste publica,
escreve no WordPress, usa rede ou altera o bloqueio do broker.
"""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from editorial_factual_certificate import (
    draft_digest,
    sign_factual_certificate,
    verify_factual_certificate,
)
from editorial_review_registry import (
    InMemorySequenceStore,
    sign_registry_envelope,
    verify_registry_envelope,
)
from editorial_trusted_review import verify_independent_review

NOW = 150
URL = "https://example.org/reviews/unico-42"
POST = {
    "id": 42, "status": "draft", "title": "Notícia verificada",
    "content": "<p>Corpo com fonte atribuída e conclusão verificável.</p>",
    "slug": "noticia-verificada", "categories": [10], "featured_media": 456,
}


def _keys():
    issuer = Ed25519PrivateKey.generate()
    registry = Ed25519PrivateKey.generate()
    return issuer, issuer.public_key(), registry, registry.public_key()


def _certificate_body(**overrides):
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


def _envelope(registry_key, *, served_at=NOW, seq=7, record=None, kid="reg-2026-11"):
    return sign_registry_envelope(
        record or _record(), served_at=served_at, registry_seq=seq,
        private_key=registry_key, kid=kid)


def _verify(cert, envelope, issuer_pub, registry_pub, store=None, *, now=NOW):
    return verify_independent_review(
        POST, cert, issuer_pub, lambda _: envelope, registry_pub,
        now=now, sequence_store=store if store is not None else InMemorySequenceStore())


def test_SEC_HAPPY_01_ed25519_certificate_and_registry_envelope():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(_certificate_body(), issuer, kid="iss-2026-11")
    assert verify_factual_certificate(POST, cert, issuer_pub, now=NOW) is True
    result = _verify(cert, _envelope(registry), issuer_pub, registry_pub,
                     InMemorySequenceStore())
    assert result == {"verified": True, "reason": None}


def test_SEC_02_certificate_signed_by_another_issuer_is_rejected():
    _, issuer_pub, registry, registry_pub = _keys()
    other = Ed25519PrivateKey.generate()
    cert = sign_factual_certificate(_certificate_body(), other, kid="iss-2026-11")
    result = _verify(cert, _envelope(registry), issuer_pub, registry_pub)
    assert result["reason"] == "certificate_invalid"


def test_SEC_03_expired_certificate_is_rejected():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(
        _certificate_body(issued_at=100, expires_at=140), issuer, kid="iss-2026-11")
    assert verify_factual_certificate(POST, cert, issuer_pub, now=NOW) is False
    assert _verify(cert, _envelope(registry), issuer_pub, registry_pub)["verified"] is False


def test_SEC_04_decision_rejected_is_not_an_approval():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(
        _certificate_body(decision="REJEITADO"), issuer, kid="iss-2026-11")
    assert verify_factual_certificate(POST, cert, issuer_pub, now=NOW) is False
    assert _verify(cert, _envelope(registry), issuer_pub, registry_pub)["verified"] is False


def test_SEC_05_wrong_review_type_is_rejected():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(
        _certificate_body(review_type="ai_generated"), issuer, kid="iss-2026-11")
    assert verify_factual_certificate(POST, cert, issuer_pub, now=NOW) is False
    assert _verify(cert, _envelope(registry), issuer_pub, registry_pub)["verified"] is False


def test_SEC_06_certificate_bound_to_another_draft_is_rejected():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(
        _certificate_body(draft_sha256=sha256(b"outro texto").hexdigest()),
        issuer, kid="iss-2026-11")
    assert verify_factual_certificate(POST, cert, issuer_pub, now=NOW) is False
    assert _verify(cert, _envelope(registry), issuer_pub, registry_pub)["verified"] is False


def test_SEC_07_envelope_without_signature_is_rejected():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(_certificate_body(), issuer, kid="iss-2026-11")
    envelope = _envelope(registry)
    envelope.pop("signature")
    assert _verify(cert, envelope, issuer_pub, registry_pub)["reason"] == (
        "review_record_signature_invalid")


def test_SEC_08_tampered_record_is_rejected():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(_certificate_body(), issuer, kid="iss-2026-11")
    envelope = _envelope(registry)
    envelope["record"]["decision"] = "REJEITADO"
    assert _verify(cert, envelope, issuer_pub, registry_pub)["reason"] == (
        "review_record_signature_invalid")


def test_SEC_09_tampered_served_at_is_rejected():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(_certificate_body(), issuer, kid="iss-2026-11")
    envelope = _envelope(registry)
    envelope["served_at"] = 151
    assert _verify(cert, envelope, issuer_pub, registry_pub)["reason"] == (
        "review_record_signature_invalid")


def test_SEC_10_tampered_registry_seq_is_rejected():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(_certificate_body(), issuer, kid="iss-2026-11")
    envelope = _envelope(registry)
    envelope["registry_seq"] = 8
    assert _verify(cert, envelope, issuer_pub, registry_pub)["reason"] == (
        "review_record_signature_invalid")


def test_SEC_11_envelope_signed_with_issuer_key_is_rejected():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(_certificate_body(), issuer, kid="iss-2026-11")
    assert _verify(cert, _envelope(issuer), issuer_pub, registry_pub)["reason"] == (
        "review_record_signature_invalid")


def test_SEC_12_stale_served_at_is_rejected():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(_certificate_body(), issuer, kid="iss-2026-11")
    envelope = _envelope(registry, served_at=NOW - 300)
    assert _verify(cert, envelope, issuer_pub, registry_pub)["reason"] == (
        "review_record_stale_response")


def test_SEC_13_future_served_at_is_rejected():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(_certificate_body(), issuer, kid="iss-2026-11")
    envelope = _envelope(registry, served_at=NOW + 60)
    assert _verify(cert, envelope, issuer_pub, registry_pub)["reason"] == (
        "review_record_stale_response")


def test_SEC_14_registry_sequence_regression_is_rejected():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(_certificate_body(), issuer, kid="iss-2026-11")
    store = InMemorySequenceStore({URL: 10})
    assert _verify(cert, _envelope(registry, seq=7), issuer_pub, registry_pub, store)[
        "reason"] == "review_record_replay_detected"


def test_SEC_36_accepted_sequence_survives_broker_restart():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(_certificate_body(), issuer, kid="iss-2026-11")
    envelope = _envelope(registry, seq=7)
    first = InMemorySequenceStore()
    assert _verify(cert, envelope, issuer_pub, registry_pub, first)["verified"] is True
    restarted = InMemorySequenceStore(first.snapshot())
    assert _verify(cert, envelope, issuer_pub, registry_pub, restarted)["reason"] == (
        "review_record_replay_detected")


def test_SEC_39_two_concurrent_requests_with_same_sequence():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(_certificate_body(), issuer, kid="iss-2026-11")
    envelope = _envelope(registry, seq=7)
    store = InMemorySequenceStore()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(
            lambda _: _verify(cert, envelope, issuer_pub, registry_pub, store),
            range(2)))
    assert sorted(r["reason"] or "verified" for r in results) == [
        "review_record_replay_detected", "verified"]


def test_SEC_42_duplicate_key_initialization_is_not_a_permissive_update():
    store = InMemorySequenceStore({URL: 7})
    envelope = _envelope(Ed25519PrivateKey.generate(), seq=7)
    assert verify_registry_envelope(
        envelope, Ed25519PrivateKey.generate().public_key(),
        now=NOW, sequence_store=store)["reason"] in (
            "review_record_signature_invalid", "review_record_replay_detected")
    assert store.snapshot() == {URL: 7}


def test_self_asserted_verified_flag_is_never_a_review():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = {"alg": "Ed25519", "verified": True, "reviewer_id": "quem-quiser"}
    result = verify_independent_review(
        POST, cert, issuer_pub, lambda _: {"verified": True}, registry_pub,
        now=NOW, sequence_store=InMemorySequenceStore())
    assert result["verified"] is False


def test_shared_secret_cannot_verify_an_ed25519_envelope():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(_certificate_body(), issuer, kid="iss-2026-11")
    result = verify_independent_review(
        POST, cert, issuer_pub, lambda _: _envelope(registry), b"x" * 32,
        now=NOW, sequence_store=InMemorySequenceStore())
    assert result["reason"] == "review_record_signature_invalid"


def test_missing_sequence_store_fails_closed():
    issuer, issuer_pub, registry, registry_pub = _keys()
    cert = sign_factual_certificate(_certificate_body(), issuer, kid="iss-2026-11")
    assert verify_registry_envelope(
        _envelope(registry), registry_pub, now=NOW, sequence_store=None)[
        "reason"] == "registry_sequence_store_missing"
