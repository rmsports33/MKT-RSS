"""
Testes P1 — estilo editorial (título/CTA/disclosure/SEO mínimo)
pytest tests/test_estilo_p1.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.landing import gerar_template_landing_page
from mkt_flow_p0.seo import validar_seo_qualidade


def test_titulo_ate_60_e_cta():
    h = gerar_template_landing_page("Fone Bluetooth JBL Pro 2026", "https://a.com", "299", status_validacao="PASS")
    assert "Ir para a Loja Oficial" in h
    assert "<h1>" in h


def test_disclosure_obrigatorio():
    h = gerar_template_landing_page("P", "https://a.com", "10", status_validacao="PASS")
    assert "#ad" in h and "comissão" in h


def test_seo_minimo_pass():
    h = gerar_template_landing_page("Review Fone Bluetooth JBL com Cancelamento de Ruído", "https://a.com",
                                    "299.90", descricao="Review completo do fone Bluetooth JBL com cancelamento de ruído ativo, bateria de 40 horas e Bluetooth 5.3 multipoint para usar no trabalho e na academia todos os dias.",
                                    status_validacao="PASS")
    c = validar_seo_qualidade(h)
    assert c["tem_title"] and c["tem_meta_desc"] and c["tem_canonical"]
