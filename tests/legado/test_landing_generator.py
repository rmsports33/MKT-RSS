"""
Testes legados — MKTFLOW.landing_generator
pytest tests/test_landing_generator.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "MKTFLOW"))
sys.path.insert(0, str(Path(__file__).parent.parent))
from MKTFLOW.landing_generator import gerar_template_landing_page, gerar_landing_page_completa, slugify


def test_template_pass():
    h = gerar_template_landing_page("Fone", "https://a.com", "99.90", status_validacao="PASS")
    assert "Ir para a Loja Oficial" in h and "#ad" in h


def test_template_bloqueado():
    assert "BLOQUEADO" in gerar_template_landing_page("F", "https://a.com", "1", status_validacao="FAIL")


def test_completa_dict():
    d = gerar_landing_page_completa("Fone JBL", "https://a.com", "199.90", status_validacao="PASS")
    assert d["slug"] == "fone-jbl" and d["html"] and d["url_amigavel"].endswith("/fone-jbl")


def test_slugify():
    assert slugify("A B!") == "a-b"
