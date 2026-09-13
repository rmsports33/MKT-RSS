"""
Testes legados — MKTFLOW.policy_engine (via adapter determinístico)
pytest tests/test_policy_engine.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "MKTFLOW"))
sys.path.insert(0, str(Path(__file__).parent.parent))
from MKTFLOW.policy_engine import avaliar_politica, construir_contexto_politica_llm, construir_contexto_minimo_llm, listar_programas


def test_programas():
    assert set(listar_programas()) == {"mercado_livre", "shopee"}


def test_fail_precede():
    r = avaliar_politica("mercado_livre", {"tipo_midia": "google_ads", "informacoes_constam_anuncio": True})
    assert r["status_politica"] == "FAIL"


def test_unknown_sem_fatos():
    assert avaliar_politica("shopee", {})["status_politica"] == "UNKNOWN"


def test_contexto_minimo():
    ctx = construir_contexto_minimo_llm("divulgar", {"usa_shortener": True}, "mercado_livre")
    assert ctx["decision"] == "FAIL" and ctx["policy"]["llm_can_override"] is False
