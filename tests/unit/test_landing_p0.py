"""
Testes P0.6 — Landing page html.escape + gate + SEO
pytest tests/test_landing_p0.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import os
from unittest.mock import patch
from mkt_flow_p0.landing import gerar_template_landing_page, slugify

def test_gate_bloqueia_unknown():
    html = gerar_template_landing_page("Prod", "https://mercadolivre.com/sec/abc?matt_word=x", "99.90", status_validacao="UNKNOWN")
    assert "BLOQUEADO" in html
    assert "href" not in html or "Ir para a Loja" not in html

def test_gate_bloqueia_fail():
    html = gerar_template_landing_page("Prod", "https://x.com", "10", status_validacao="FAIL")
    assert "BLOQUEADO" in html

def test_gate_permite_pass():
    html = gerar_template_landing_page("Prod Teste", "https://mercadolivre.com/sec/abc?matt_word=x", "99.90", status_validacao="PASS")
    assert "Prod Teste" in html
    assert "Ir para a Loja Oficial" in html
    assert "#ad #linkdeafiliado" in html

def test_xss_escape():
    html = gerar_template_landing_page('<script>alert(1)</script>', 'https://x.com?a="b"', '99.90', status_validacao="PASS")
    # Payload do usuário deve sair escapado (GA/schema legítimos contêm <script>,
    # e test_e2e importa pipeline_p0 que carrega .env real com GA — ver nota refactor)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "&quot;" in html or "a=&quot;b" in html

def test_seo_tags():
    html = gerar_template_landing_page("Fone JBL", "https://a.com", "199.90", descricao="Fone com som potente", status_validacao="PASS")
    assert '<meta name="description"' in html
    assert '<meta property="og:title"' in html
    assert '"@type": "Product"' in html
    assert 'rel="canonical"' in html

def test_slug():
    assert slugify("Fone JBL 123!") == "fone-jbl-123"
    assert slugify("  ") == "produto"

def test_ga_injetado_quando_measurement_id_presente():
    with patch.dict(os.environ, {"GA_MEASUREMENT_ID": "G-XXXXXXXXXX"}):
        html = gerar_template_landing_page("Prod", "https://a.com", "10", status_validacao="PASS")
        assert "googletagmanager.com" in html
        assert "G-XXXXXXXXXX" in html
        assert "affiliate_click" in html
        assert 'data-ga=' in html

def test_ga_ausente_sem_measurement_id():
    with patch.dict(os.environ, {"GA_MEASUREMENT_ID": ""}):
        html = gerar_template_landing_page("Prod", "https://a.com", "10", status_validacao="PASS")
        assert "googletagmanager.com" not in html

if __name__ == "__main__":
    for n, fn in list(globals().items()):
        if n.startswith("test_"):
            fn()
            print(f"[OK] {n}")
    print("Todos P0.6 passaram")
