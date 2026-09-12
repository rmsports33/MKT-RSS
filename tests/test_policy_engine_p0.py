"""
Testes P0 — policy engine determinístico (21 regras)
pytest tests/test_policy_engine_p0.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.policy_engine import avaliar_politica, construir_contexto_politica_llm, POLICY_RULES


def test_21_regras_carregadas():
    assert len(POLICY_RULES) == 21


def test_ml_search_ads_fail():
    r = avaliar_politica("mercado_livre", {"tipo_midia": "google_ads"})
    assert r["status_politica"] == "FAIL"
    assert r["regras"][0]["regra_id"] == "ML-PAID-SEARCH"


def test_ml_social_pass():
    r = avaliar_politica("mercado_livre", {"tipo_midia": "tiktok_ads", "midia_cadastrada": True, "titularidade_afiliado": True})
    assert r["status_politica"] == "PASS"


def test_ml_api_publica_unknown():
    r = avaliar_politica("mercado_livre", {"usa_api_publica_ml": True})
    assert r["status_politica"] == "UNKNOWN"


def test_shopee_indexacao_fail():
    r = avaliar_politica("shopee", {"url_afiliada_com_id": True, "indexacao_organica": True})
    assert r["status_politica"] == "FAIL"


def test_shopee_extracao_sem_auth_fail():
    r = avaliar_politica("shopee", {"consulta_automatizada_shopee": True, "autorizacao_api": False})
    assert r["status_politica"] == "FAIL"


def test_programa_desconhecido_unknown():
    r = avaliar_politica("amazon", {})
    assert r["status_politica"] == "UNKNOWN"


def test_contexto_llm_minimo():
    r = avaliar_politica("mercado_livre", {"usa_shortener": True})
    ctx = construir_contexto_politica_llm(r)
    assert ctx["llm_can_override"] is False
    assert "ML-SHORTENER" in ctx["reason_codes"]
