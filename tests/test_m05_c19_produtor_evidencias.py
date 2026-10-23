from mkt_flow_p0.produtor_evidencias_noticia import produzir_contrato_noticia


def snapshot():
    return {
        "contract_version": "1.0", "content_type": "noticia", "status": "PASS",
        "sources": [{"id": "s1", "url": "https://example.org/relatorio",
                     "retrieved_at": "2026-10-22", "status": "PASS"}],
        "claims": [{"id": "c1", "status": "PASS", "evidence_ids": ["s1"],
                    "text": "A empresa apresentou o dispositivo."}],
    }


def test_approved_evidence_and_exact_text():
    assert produzir_contrato_noticia(snapshot(), "A empresa apresentou o dispositivo.") is not None


def test_missing_evidence_is_blocked():
    assert produzir_contrato_noticia(None, "A empresa apresentou o dispositivo.") is None


def test_claim_not_present_is_blocked():
    assert produzir_contrato_noticia(snapshot(), "Outro assunto.") is None


def test_unknown_claim_is_blocked():
    data = snapshot()
    data["claims"][0]["status"] = "UNKNOWN"
    assert produzir_contrato_noticia(data, "A empresa apresentou o dispositivo.") is None


def test_missing_claim_text_is_blocked():
    data = snapshot()
    del data["claims"][0]["text"]
    assert produzir_contrato_noticia(data, "A empresa apresentou o dispositivo.") is None


def test_original_evidence_is_not_mutated():
    data = snapshot()
    produzir_contrato_noticia(data, "A empresa apresentou o dispositivo.")
    assert data["claims"][0]["status"] == "PASS"
