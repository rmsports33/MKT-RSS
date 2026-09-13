"""
Testes legados — MKTFLOW.seo_programmatic
pytest tests/test_seo_programmatic.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "MKTFLOW"))
sys.path.insert(0, str(Path(__file__).parent.parent))
from MKTFLOW.seo_programmatic import generate_programmatic_pages, build_sitemap, get_seo_stats


def test_gera_paginas_reais():
    prods = [{"nome": "Fone JBL", "preco": "299.90"}, {"nome": "", "preco": ""}, {"nome": "Mouse", "preco": "99"}]
    pags = generate_programmatic_pages(prods)
    assert len(pags) == 2 and all(p["slug"] for p in pags)


def test_sitemap_e_stats():
    xml = build_sitemap(["https://site.com/a"])
    assert "<urlset" in xml
    st = get_seo_stats([{"titulo": "Um título com mais de dez chars"}, {"titulo": "x"}])
    assert st["total_paginas"] == 2 and st["com_titulo_ok"] == 1
