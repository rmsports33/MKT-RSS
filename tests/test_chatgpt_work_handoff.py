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


def test_traducao_mapeada_pede_revisao_semantica_sem_liberar_wp():
    contrato, capturas = dados()
    contrato["claims"][0]["text"] = "The update was announced."
    capturas["s1"]["texto"] = "Official release: The update was announced."
    pacote = preparar_pacote(contrato, capturas)
    resposta = {
        "texto_markdown": "A atualização foi anunciada.",
        "referencias_traducao": {
            "a atualização foi anunciada.": ["c1"],
        },
    }
    revisao = avaliar_retorno(pacote, resposta)
    cobertura = revisao["auditoria_cobertura"]
    assert cobertura["veredito"] == "REVISAO_SEMANTICA_PENDENTE"
    assert cobertura["candidatas_traducao"][0]["claim_ids"] == ["c1"]
    assert revisao["acao"] == "bloqueado"
    assert revisao["escreveu"] is False
    assert revisao["verificacao_factual"] == "NAO_VERIFICADO"
    assert revisao["revisao_humana_pendente"] is True


def test_referencia_inventada_nao_concede_correspondencia():
    pacote = preparar_pacote(*dados())
    resposta = {
        "texto_markdown": "Foi lançado no Brasil por R$ 999.",
        "referencias_traducao": {
            "foi lançado no brasil por r$ 999.": ["claim-inexistente"],
        },
    }
    revisao = avaliar_retorno(pacote, resposta)
    assert revisao["auditoria_cobertura"]["veredito"] == "BLOQUEADO"
    assert revisao["auditoria_cobertura"]["sem_referencia"] == 1
    assert revisao["escreveu"] is False


def test_parafrase_sem_mapeamento_continua_bloqueada():
    pacote = preparar_pacote(*dados())
    revisao = avaliar_retorno(pacote, {
        "texto_markdown": "Houve anúncio de atualização.",
    })
    assert revisao["auditoria_cobertura"]["veredito"] == "BLOQUEADO"
    assert revisao["revisao_humana_pendente"] is True
