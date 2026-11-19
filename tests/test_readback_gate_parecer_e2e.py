"""Simulated end-to-end readback and parecer handoff, using existing modules only.

No WordPress, Turso, network, credentials or writes. The native REST shapes and
the owner-release packet are fixtures; the producer marker, readback adapter,
trusted reviewer and Gate packet validator are the real implementations.
"""
import hashlib
import hmac
import json

import pytest

from editorial_factual_certificate import draft_digest
from editorial_publish_gate import authorize_publish
from editorial_trusted_review import verify_independent_review
from editorial_wordpress_adapter import (
    assemble_wordpress_context_readback,
    validate_wordpress_content_readback,
)
from mkt_flow_p0.gate_unified import (
    GATE_CHECKS,
    GateBlocked,
    advisory_gate_receipt,
    content_digest,
    readiness_overview,
    read_owner_release,
    validate_owner_release,
)
from mkt_flow_p0.editorial_provenance import (
    MODULOS_OBRIGATORIOS,
    marcar,
    version_sha256_esperado,
)

KEY = b"test-only-key-for-simulated-trusted-review-123456"
POST_ID = 42
MODIFIED = "2026-11-19T10:00:00"
TITLE = "Título verificado para leitura nativa"
SLUG = "leitura-nativa-verificada"


def _producer_body():
    return marcar(
        "<h2>Análise verificada</h2>\n<p>Corpo com fonte atribuída e conclusão.</p>",
        modules={name: "EXECUTED" for name in MODULOS_OBRIGATORIOS},
        voice_status="ASSISTED_ADAPTED",
        substance_status="PASS",
        image_rights_confirmed=True,
        version_sha256=version_sha256_esperado(),
    )[0]


def _rest_pair(body):
    """Native WordPress REST shapes: edit exposes raw, view exposes rendered."""
    edit = {
        "id": POST_ID, "status": "draft", "modified": MODIFIED,
        "title": {"raw": TITLE, "rendered": TITLE},
        "slug": SLUG, "categories": [10], "featured_media": 456,
        "link": "https://conexotech.com.br/?p=42",
        "meta": {"_conexo_mkt_rss_run_id": "run-simulada-001"},
        "content": {"raw": body, "rendered": body},
    }
    view = {
        "id": POST_ID, "status": "draft", "modified": MODIFIED,
        "title": TITLE, "slug": SLUG, "categories": [10], "featured_media": 456,
        "link": "https://conexotech.com.br/?p=42",
        "content": {"rendered": body},
    }
    return edit, view


def _certificate_and_record(post):
    cert = {
        "version": 1, "review_type": "independent_human",
        "draft_sha256": draft_digest(post), "decision": "APROVADO",
        "reviewer_id": "revisor-unico-3",
        "review_record_url": "https://example.org/reviews/unico-42",
        "evidence_refs": ["https://example.org/source"],
        "issued_at": 100, "expires_at": 200,
    }
    payload = json.dumps(cert, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode()
    cert["signature"] = hmac.new(KEY, payload, hashlib.sha256).hexdigest()
    record = {
        "reviewer_id": cert["reviewer_id"],
        "review_record_url": cert["review_record_url"],
        "draft_sha256": cert["draft_sha256"], "decision": "APROVADO",
        "status": "FINAL", "independent": True, "revoked": False,
        "evidence_refs": cert["evidence_refs"],
    }
    return cert, record


def _release(body, *, post_id=POST_ID, content=None):
    return {
        "schema": "conexo-owner-release/1",
        "version_sha256": version_sha256_esperado(),
        "payload": {
            "article_id": "wp:%d" % post_id,
            "content": body if content is None else content,
            "title": TITLE, "slug": SLUG,
            "wordpress": {"post_id": post_id, "featured_media": 456,
                          "categories": [10]},
            "owner_id": 3, "review_mode": "owner",
            "approval_reference": "SIMULATED-OWNER-42",
            "checks": {
                key: {"estado": "VERIFICADO",
                      "evidencia": ["Evidência simulada suficiente " + key]}
                for key in GATE_CHECKS
            },
        },
    }


def _readback():
    body = _producer_body()
    edit, view = _rest_pair(body)
    combined, blockers = assemble_wordpress_context_readback(edit, view)
    assert blockers == []
    assert validate_wordpress_content_readback(combined)["valid"] is True
    return combined, body


def test_native_readback_trusted_review_and_gate_packet_share_exact_version():
    combined, body = _readback()
    cert, record = _certificate_and_record(combined)
    assert verify_independent_review(
        combined, cert, KEY, lambda _: record, now=150)["verified"] is True

    release = _release(body)
    info = validate_owner_release(release, post_id=POST_ID)
    assert info["content_sha256"] == content_digest(body)
    assert info["version_sha256"] == version_sha256_esperado()

    result = authorize_publish(
        combined,
        {"verified": True, "reviewer_id": cert["reviewer_id"]},
        owner_release=release,
    )
    assert "editorial_provenance_content_raw_unavailable" not in result["bloqueios"]
    assert "gate_owner_release_missing" not in result["bloqueios"]
    assert "remote_version_mismatch" not in result["bloqueios"]
    # Sem pacote canônico e sem core confiável nada é autorizado automaticamente.
    assert result["autorizado"] is False
    assert result["bloqueios"] == [
        "canonical_editorial_package_missing", "trusted_factual_review_missing"
    ]


def test_reviewer_verification_alone_never_authorizes_publication():
    combined, _ = _readback()
    cert, record = _certificate_and_record(combined)
    assert verify_independent_review(
        combined, cert, KEY, lambda _: record, now=150)["verified"] is True

    result = authorize_publish(
        combined, {"verified": True, "reviewer_id": cert["reviewer_id"]})
    assert result["autorizado"] is False
    assert "gate_owner_release_missing" in result["bloqueios"]

    overview = readiness_overview(conteudo={"status": "completo"},
                                  wordpress={"status": "readback_ok"},
                                  recibos={"owner_release": "validado"})
    assert overview["publication_authorized"] is False


def test_release_bound_to_different_content_is_rejected():
    combined, body = _readback()
    release = _release(body, content=body + "\n<!-- adulterado -->")
    result = authorize_publish(combined, {"verified": True}, owner_release=release)
    assert result["autorizado"] is False
    assert "remote_version_mismatch" in result["bloqueios"]


def test_release_for_another_post_is_rejected():
    combined, body = _readback()
    release = _release(body, post_id=43)
    result = authorize_publish(combined, {"verified": True}, owner_release=release)
    assert result["autorizado"] is False
    assert "gate_owner_release_post_mismatch" in result["bloqueios"]


def test_http_200_with_invalid_packet_is_not_semantic_validation():
    class Response:
        status_code = 200

        def json(self):
            return {"schema": "conexo-owner-release/1", "payload": {}}

    class Session:
        def get(self, *args, **kwargs):
            return Response()

    with pytest.raises(GateBlocked, match="OWNER_PACKET_INVALID"):
        read_owner_release(POST_ID, session=Session(), auth=("user", "password"))


def test_advisory_receipt_binds_to_the_exact_raw_body():
    _, body = _readback()
    info = validate_owner_release(_release(body), post_id=POST_ID)
    receipt = advisory_gate_receipt(info, markdown=body, date="2026-11-19T00:00:00+00:00")
    assert receipt["content_sha256"] == content_digest(body)
    assert receipt["reviewer"] == "wordpress-gate-owner-3"
    assert "publication_authorized" not in receipt


# --- Revisor Único ligado ao guard: pacote + recibo + parecer na mesma versão ---

def _package(body, *, post_id=POST_ID):
    return {
        "stage": "ready",
        "version_sha256": version_sha256_esperado(),
        "payload": {
            "title": TITLE, "slug": SLUG, "content": body,
            "wordpress": {"post_id": post_id, "featured_media": 456,
                          "categories": [10]},
        },
    }


class _SimulatedCore:
    """Stands in for the hash-pinned Conexo OS validator; no file is read."""

    class _Validator:
        def evaluate(self, package, root, *, require_editorial_ready=True):
            return [], []

    def validator(self):
        return self._Validator()


def _patch_core(monkeypatch):
    monkeypatch.setattr("mkt_flow_p0.editorial_transport.load_core",
                        lambda root: _SimulatedCore())


def test_verified_review_with_valid_package_and_release_authorizes_simulated(
        monkeypatch, tmp_path):
    combined, body = _readback()
    cert, record = _certificate_and_record(combined)
    _patch_core(monkeypatch)
    result = authorize_publish(
        combined, {"verified": True},
        package=_package(body), core_root=str(tmp_path),
        owner_release=_release(body),
        review_certificate=cert, review_signing_key=KEY,
        lookup_review=lambda _: record, now=150)
    assert result == {"autorizado": True, "bloqueios": []}


def test_valid_package_and_release_without_verified_review_stay_blocked(
        monkeypatch, tmp_path):
    combined, body = _readback()
    _patch_core(monkeypatch)
    result = authorize_publish(
        combined, {"verified": True},
        package=_package(body), core_root=str(tmp_path),
        owner_release=_release(body))
    assert result["autorizado"] is False
    assert "trusted_factual_review_missing" in result["bloqueios"]


def test_revoked_review_blocks_even_with_valid_package_and_release(
        monkeypatch, tmp_path):
    combined, body = _readback()
    cert, record = _certificate_and_record(combined)
    _patch_core(monkeypatch)
    result = authorize_publish(
        combined, {"verified": True},
        package=_package(body), core_root=str(tmp_path),
        owner_release=_release(body),
        review_certificate=cert, review_signing_key=KEY,
        lookup_review=lambda _: {**record, "revoked": True}, now=150)
    assert result["autorizado"] is False
    assert "trusted_factual_review_review_record_mismatch" in result["bloqueios"]


def test_self_asserted_review_dict_is_never_verification():
    combined, _ = _readback()
    result = authorize_publish(
        combined, {"verified": True, "reviewer_id": "revisor-unico-3"})
    assert result["autorizado"] is False
    assert "trusted_factual_review_missing" in result["bloqueios"]
