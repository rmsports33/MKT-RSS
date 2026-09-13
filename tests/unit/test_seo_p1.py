"""
Testes P1 — SEO (templates, sitemap, FAQ)
pytest tests/test_seo_p1.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.seo import template_por_categoria, gerar_sitemap, gerar_faq_schema, gerar_faq_review, canonical_url


def test_template_categoria():
    t = template_por_categoria("eletronicos", "Fone JBL", "299.90")
    assert len(t["title"]) <= 60 and "Fone JBL" in t["h1"]


def test_sitemap():
    xml = gerar_sitemap(["https://site.com/a", "oferta-b"])
    assert "<urlset" in xml and "https://site.com/a" in xml and "oferta-b" in xml


def test_faq_schema():
    faqs = gerar_faq_review("Fone JBL", "299.90")
    sch = gerar_faq_schema(faqs)
    assert "FAQPage" in sch and "vale a pena" in sch


def test_canonical():
    assert canonical_url("Fone JBL!", "https://site.com") == "https://site.com/fone-jbl"
