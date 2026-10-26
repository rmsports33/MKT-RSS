from copy import deepcopy
import pytest

from mkt_flow_p0.chatgpt_work_handoff import preparar_pacote, avaliar_retorno

URL = "https://example.org/source"
CLAIM = "A atualização foi anunciada."

def dados():
    contrato = {
        "contract_version": "1.0", "content_type": "noticia", "status": "PASS",
        "sources": [{"id": "s1", "url": URL, "status": "PASS",
                     "retrieved_at": "2026-10-26"}],
        "claims": [{"id": "c1", "text": CLAIM, "status": "PASS",
                    "evidence_ids": ["s1"]}],
    }
    capturas = {"s1": {"url": URL, "texto": "Comunicado. " + CLAIM}}
    return contrato, capturas

def test_handoff_review_never_authorizes_wp():
    contrato, capturas = dados()
    pacote = preparar_pacote(contrato, capturas)
    resultado = avaliar_retorno(pacote, {"texto_markdown": CLAIM})
    assert resultado["auditoria_cobertura"]["veredito"] == "COBERTURA_LITERAL"
    assert resultado["acao"] == "bloqueado"
    assert resultado["escreveu"] is False
    assert resultado["verificacao_factual"] == "NAO_VERIFICADO"

def test_added_claim_flagged():
    pacote = preparar_pacote(*dados())
    resultado = avaliar_retorno(pacote, {"texto_markdown": CLAIM + " Custa R$ 999."})
    assert resultado["auditoria_cobertura"]["veredito"] == "BLOQUEADO"

def test_package_tampering_failclosed():
    pacote = preparar_pacote(*dados())
    pacote["payload"]["capturas"]["s1"]["texto"] = "texto adulterado"
    resultado = avaliar_retorno(pacote, {"texto_markdown": CLAIM})
    assert resultado["auditoria_cobertura"]["veredito"] == "BLOQUEADO"

def test_missing_captures_rejected():
    contrato, _ = dados()
    with pytest.raises(ValueError):
        preparar_pacote(contrato, None)

def test_unapproved_claim_rejected():
    contrato, capturas = dados()
    contrato["claims"][0]["status"] = "UNKNOWN"
    with pytest.raises(ValueError):
        preparar_pacote(contrato, capturas)

def test_empty_response_failclosed():
    pacote = preparar_pacote(*dados())
    assert avaliar_retorno(pacote, {"texto_markdown": ""})["acao"] == "bloqueado"
