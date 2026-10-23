from mkt_flow_p0.contrato_evidencias_noticia import avaliar_evidencias


def test_missing_contract_is_blocked():
    assert avaliar_evidencias(None)["veredito"] == "BLOQUEADO"


def test_unverified_claim_is_blocked():
    payload = {
        "contract_version": "1.0",
        "content_type": "noticia",
        "status": "PASS",
        "sources": [{"id": "s1", "status": "PASS", "url": "https://example.org",
                     "retrieved_at": "2026-10-22"}],
        "claims": [{"id": "c1", "status": "UNKNOWN", "evidence_ids": ["s1"]}],
    }
    assert avaliar_evidencias(payload)["veredito"] == "BLOQUEADO"


def test_approved_structure_is_not_factual_pass():
    payload = {
        "contract_version": "1.0",
        "content_type": "noticia",
        "status": "PASS",
        "sources": [{"id": "s1", "status": "PASS", "url": "https://example.org",
                     "retrieved_at": "2026-10-22"}],
        "claims": [{"id": "c1", "status": "PASS", "evidence_ids": ["s1"]}],
    }
    assert avaliar_evidencias(payload)["veredito"] == "EVIDENCIAS_ESTRUTURADAS"
