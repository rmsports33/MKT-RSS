from mkt_flow_p0.lastro_offline_noticia import auditar_lastro_offline


def contrato():
    return {
        "contract_version": "1.0", "content_type": "noticia", "status": "PASS",
        "sources": [{"id": "s1", "url": "https://example.org/fonte",
                     "retrieved_at": "2026-10-22", "status": "PASS"}],
        "claims": [{"id": "c1", "status": "PASS", "evidence_ids": ["s1"],
                    "text": "A empresa apresentou o dispositivo."}],
    }


def capturas():
    return {"s1": {"url": "https://example.org/fonte",
                   "texto": "A empresa apresentou o dispositivo."}}


def test_lastro_literal_nao_equivale_a_pass_factual():
    assert auditar_lastro_offline(contrato(), capturas())["veredito"] == "LASTRO_LITERAL"


def test_sem_capturas_bloqueia():
    assert auditar_lastro_offline(contrato(), None)["veredito"] == "BLOQUEADO"


def test_url_diferente_bloqueia():
    dados = capturas()
    dados["s1"]["url"] = "https://outra.example.org"
    assert "url_captura_divergente" in auditar_lastro_offline(contrato(), dados)["motivos"]


def test_claim_inventado_bloqueia():
    dados = capturas()
    dados["s1"]["texto"] = "A empresa apresentou outra coisa."
    assert "claim_sem_lastro_literal" in auditar_lastro_offline(contrato(), dados)["motivos"]


def test_claim_nao_aprovado_bloqueia():
    c = contrato()
    c["claims"][0]["status"] = "UNKNOWN"
    assert auditar_lastro_offline(c, capturas())["veredito"] == "BLOQUEADO"


def test_pipeline_exige_injecao_explicita_e_nao_liga_wp():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "pipeline_rss.py").read_text(encoding="utf-8")
    assert "evidencias_aprovadas: dict = None" in source
    assert "capturas_aprovadas: dict = None" in source
    assert "auditar_lastro_offline" in source
    assert '"escreveu": False' in source
