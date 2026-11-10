import base64
import hashlib
import json
import zipfile

import pytest

from scripts.audit_live_handoff_evidence import EvidenceAuditError, audit_artifact
from scripts.handoff_live_once import assess_handoff_quality
from mkt_flow_p0.editorial_substance import CRITERIA, brief_hash, content_hash


BRIEF = {
    "genre": "guia",
    "reader": "Pessoas que precisam identificar a configuração antes de alterá-la.",
    "need": "Distinguir comportamentos parecidos no teclado antes de escolher um ajuste.",
    "angle": "Separar os cenários e explicar os custos de cada intervenção.",
    "contribution": "Orientar uma mudança reversível por vez, com ressalvas de versões.",
    "limits": "Sem teste próprio; instruções e disponibilidade dependem do fabricante.",
}
ARTICLE = (
    "## Escolha pelo problema\n\n"
    "Antes de mudar controles de teclado, diferencie a palavra substituída de "
    "uma sugestão exibida ao digitar. O custo de remover uma sugestão é também "
    "perder uma ajuda que pode ser conveniente em outros contextos.\n\n"
    "## Revise a mudança\n\n"
    "Experimente mudar uma configuração de cada vez e observe o efeito "
    "sem concluir que essa recomendação substitui documentação técnica. "
    "Este artigo não foi validado em um aparelho real."
)


def valid_critique():
    return {
        "method": "assisted",
        "reviewer": "test-provider-not-human",
        "content_sha256": content_hash(ARTICLE),
        "brief_sha256": brief_hash(BRIEF),
        "criteria": {
            key: {
                "score": 3,
                "reason": "A justificativa explica a opção do leitor, mas não é um aceite factual.",
                "excerpt": ARTICLE.split("\n\n")[1],
            }
            for key in CRITERIA
        },
    }


def test_handoff_technical_success_without_review_is_not_green_editorial():
    packet = {"markdown": ARTICLE, "metadata": {"editorial_brief": BRIEF}}
    status = assess_handoff_quality(packet, "PRONTO_PARA_REVISAO_HUMANA", [])
    assert status["status"] == "PENDING"
    assert status["review_valid"] is False
    assert status["publication_authorized"] is False


def test_valid_assisted_review_is_only_ready_for_human_not_publication():
    packet = {"markdown": ARTICLE, "metadata": {
        "editorial_brief": BRIEF, "editorial_substance_review": valid_critique()}}
    quality = assess_handoff_quality(packet, "PRONTO_PARA_REVISAO_HUMANA", [])
    assert quality["status"] == "READY_FOR_HUMAN_REVIEW"
    assert quality["publication_authorized"] is False
    pending_image = assess_handoff_quality(
        packet, "ENRIQUECIMENTO_PENDENTE", ["imagem_destacada_com_direitos_pendente"])
    assert pending_image["status"] == "PENDING"


def make_archive(path, *, tamper=False):
    manifest = {
        "schema": "mkt-live-handoff-receipt/1",
        "outcome": "HANDOFF_CREATED",
        "process_exit_code": 0,
        "expected_results": 1,
        "wordpress_written": False,
        "review_method": None,
        "substantive_scores": {},
        "quality_status": "ENRIQUECIMENTO_PENDENTE",
        "quality_pending": [
            "avaliacao_substantiva_ausente_invalida_ou_desatualizada",
            "pesquisa_multifonte_pendente",
        ],
    }
    ciphertext = b"encrypted fixture, no article"
    encrypted = {
        "schema": "mkt-handoff-live/1",
        "nonce": base64.b64encode(b"123456789012").decode(),
        "wrapped_key": base64.b64encode(b"dummy-wrapped-key").decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "ciphertext_sha256": "0" * 64 if tamper else
            hashlib.sha256(ciphertext).hexdigest(),
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest))
        z.writestr("handoff-encrypted.json", json.dumps(encrypted))


def test_audit_historical_handoff_does_not_claim_recovered_source_or_approval(tmp_path):
    path = tmp_path / "legacy.zip"
    make_archive(path)
    result = audit_artifact(path)
    assert result["archive_integrity"] == "PASS"
    assert result["technical_handoff_created"] is True
    assert result["plaintext_decrypted"] is False
    assert result["editorial_readiness_claim"] == "PENDING"
    assert result["substantive_review_receipt"] == "ABSENT_OR_INVALID"
    assert result["provider_cause_of_historical_failure"] == "NOT_RECORDED"
    assert result["independent_review_completed"] is False
    assert result["source_verification_completed"] is False
    assert result["image_rights_confirmed"] is False
    assert result["publication_authorized"] is False
    assert "encrypted fixture" not in json.dumps(result)


def test_audit_rejects_tampered_ciphertext_digest(tmp_path):
    path = tmp_path / "tampered.zip"
    make_archive(path, tamper=True)
    with pytest.raises(EvidenceAuditError, match="CIPHERTEXT_HASH_MISMATCH"):
        audit_artifact(path)
