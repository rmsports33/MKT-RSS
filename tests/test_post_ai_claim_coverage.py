from mkt_flow_p0.auditoria_cobertura_pos_ia import auditar_cobertura_pos_ia

URL = "https://example.org/source"
CLAIM = "O produto recebeu uma atualização."

def dados():
    contrato = {
        "contract_version": "1.0", "content_type": "noticia", "status": "PASS",
        "sources": [{"id": "s1", "status": "PASS", "url": URL,
                     "retrieved_at": "2026-10-26"}],
        "claims": [{"id": "c1", "status": "PASS", "text": CLAIM,
                    "evidence_ids": ["s1"]}],
    }
    capturas = {"s1": {"url": URL, "texto": "Anúncio: " + CLAIM}}
    return contrato, capturas

def test_literal_claim_not_factual_authorization():
    contrato, capturas = dados()
    r = auditar_cobertura_pos_ia(CLAIM, contrato, capturas)
    assert r["veredito"] == "COBERTURA_LITERAL"
    assert r["autoriza_wordpress"] is False
    assert r["certificacao_factual"] is False

def test_invented_assertion_blocked():
    contrato, capturas = dados()
    r = auditar_cobertura_pos_ia(CLAIM + " O produto custa R$ 99.", contrato, capturas)
    assert r["veredito"] == "BLOQUEADO"
    assert r["sem_correspondencia"] == 1

def test_invalid_capture_blocked():
    contrato, capturas = dados()
    capturas["s1"]["texto"] = "Nada disso foi comprovado"
    r = auditar_cobertura_pos_ia(CLAIM, contrato, capturas)
    assert r["veredito"] == "BLOQUEADO"

def test_no_capture_blocked():
    contrato, _ = dados()
    assert auditar_cobertura_pos_ia(CLAIM, contrato, None)["veredito"] == "BLOQUEADO"

def test_pending_claim_blocked():
    contrato, capturas = dados()
    contrato["claims"][0]["status"] = "UNKNOWN"
    assert auditar_cobertura_pos_ia(CLAIM, contrato, capturas)["veredito"] == "BLOQUEADO"

def test_no_generated_text_blocked():
    contrato, capturas = dados()
    assert auditar_cobertura_pos_ia("", contrato, capturas)["veredito"] == "BLOQUEADO"
