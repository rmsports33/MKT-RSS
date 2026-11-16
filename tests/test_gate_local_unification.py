"""Regressões da unificação do gate local com o Gate único do WordPress.

Cobre D8 (o gate local passa a exigir o aceite humano emitido pelo Gate) e
D16 (o comprovante advisory ``wordpress_gate_test`` passa a ter produtor).
"""
import pytest

from editorial_publish_gate import authorize_publish
from mkt_flow_p0.gate_unified import (GATE_CHECKS, advisory_gate_receipt,
                                       content_digest, read_owner_release,
                                       validate_owner_release)

VERSION = "c" * 64

POST = {"id": 9768, "status": "draft", "categories": [10],
        "slug": "noticia-verificada", "featured_media": 456,
        "title": "Notícia verificada", "content": "<p>Texto confirmado</p>",
        "link": "https://conexotech.com.br/?p=9768"}
REVIEW = {"veredito": "APROVADO", "revisao_substantiva": True,
          "evidencias_verificadas": True, "aprovacao_atual": True}


def owner_release(post_id=9768, content="<p>Texto confirmado</p>"):
    return {
        "schema": "conexo-owner-release/1",
        "version_sha256": VERSION,
        "payload": {
            "article_id": "wp:" + str(post_id),
            "content": content,
            "title": "Notícia verificada",
            "slug": "noticia-verificada",
            "wordpress": {"post_id": post_id},
            "owner_id": 3,
            "review_mode": "owner",
            "approval_reference": "OWNER-3-%d-SYNTHETIC" % post_id,
            "checks": {key: {"estado": "VERIFICADO",
                             "evidencia": ["Synthetic human review " + key]}
                       for key in GATE_CHECKS},
            "seo": {"provider": "native",
                    "canonical": "https://conexotech.com.br/noticia-verificada/",
                    "title": "Notícia verificada",
                    "description": "Descrição verificada."},
        },
    }


# --- D8: o gate local exige o aceite humano do Gate --------------------------

def test_publication_without_gate_release_is_blocked():
    result = authorize_publish(POST, REVIEW)
    assert result["autorizado"] is False
    assert "gate_owner_release_missing" in result["bloqueios"]


def test_invalid_gate_release_is_blocked():
    release = owner_release()
    release["payload"]["owner_id"] = 4
    result = authorize_publish(POST, REVIEW, owner_release=release)
    assert result["autorizado"] is False
    assert "gate_owner_release_invalid" in result["bloqueios"]


def test_gate_release_for_another_post_is_blocked():
    result = authorize_publish(POST, REVIEW, owner_release=owner_release(9810))
    assert result["autorizado"] is False
    assert "gate_owner_release_post_mismatch" in result["bloqueios"]


def test_edited_content_invalidates_the_gate_release():
    release = owner_release(content="<p>Texto editado depois do aceite</p>")
    result = authorize_publish(POST, REVIEW, owner_release=release)
    assert result["autorizado"] is False
    assert "remote_version_mismatch" in result["bloqueios"]


def test_blockers_are_not_repeated():
    result = authorize_publish(POST, REVIEW, owner_release=owner_release(
        content="<p>Texto editado depois do aceite</p>"))
    assert len(result["bloqueios"]) == len(set(result["bloqueios"]))


def test_technical_checks_never_replace_the_human_acceptance():
    # O parecer local é completo e o pacote canônico está ausente: ainda assim
    # o Gate local bloqueia, porque o aceite humano do Gate não foi apresentado.
    result = authorize_publish(POST, REVIEW)
    assert result["autorizado"] is False


# --- D16: produtor do comprovante advisory wordpress_gate_test --------------

def test_advisory_receipt_is_produced_from_the_gate_release():
    info = validate_owner_release(owner_release())
    receipt = advisory_gate_receipt(info, date="2026-11-16T00:00:00+00:00")
    assert receipt["status"] == "approved"
    assert receipt["content_sha256"] == info["content_sha256"]
    assert receipt["reviewer"] == "wordpress-gate-owner-3"
    assert receipt["evidence"].startswith("owner-release:")
    assert info["version_sha256"] in receipt["evidence"]
    assert receipt["date"] == "2026-11-16T00:00:00+00:00"


def test_advisory_receipt_is_accepted_by_the_voice_gate():
    from mkt_flow_p0.editorial_voice_adapter import editorial_readiness
    markdown = "Artigo completo"
    info = validate_owner_release(owner_release(content="<p>Texto confirmado</p>"))
    receipts = {"wordpress_gate_test": advisory_gate_receipt(info, markdown=markdown)}
    result = editorial_readiness(markdown, receipts)
    assert "wordpress_gate_test" not in result["missing_receipts"]
    assert result["publication_authorized"] is False
    assert result["ready_for_gate"] is False


def test_advisory_receipt_requires_a_valid_release():
    with pytest.raises(Exception):
        advisory_gate_receipt({"content_sha256": "nao-e-sha"})


# --- D6: digest unico -------------------------------------------------------

def test_content_digest_is_the_single_text_digest():
    import hashlib
    assert content_digest("<p>Texto confirmado</p>") == hashlib.sha256(
        "<p>Texto confirmado</p>".encode("utf-8")).hexdigest()
    with pytest.raises(Exception):
        content_digest(None)
