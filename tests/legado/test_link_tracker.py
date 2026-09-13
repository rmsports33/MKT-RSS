"""
Testes legados — MKTFLOW.link_tracker + orchestrator (mocks)
pytest tests/test_link_tracker.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent.parent / "MKTFLOW"))
sys.path.insert(0, str(Path(__file__).parent.parent))
from MKTFLOW.link_tracker import create_campaign, register_publication, get_link_history, list_links, detect_link_conflicts, get_campaign_report
from MKTFLOW.orchestrator import run_pipeline


def test_campaign_e_publication():
    c = create_campaign("camp-teste", "mercado_livre")
    p = register_publication(c["campaign_id"], "https://ml.com/p/1", "wordpress", "https://site.com/1")
    assert p["campaign_id"] == c["campaign_id"]
    assert len(get_link_history("https://ml.com/p/1")) >= 1
    assert get_campaign_report(c["campaign_id"])["total"] >= 1


def test_conflicts_duplicado():
    register_publication("cx", "https://ml.com/dup", "wordpress", "https://site.com/d1")
    register_publication("cx", "https://ml.com/dup", "wordpress", "https://site.com/d2")
    assert any(x["tipo"] == "duplicado" for x in detect_link_conflicts("https://ml.com/dup"))


def test_orchestrator_mockado():
    fake_ml = {"titulo": "P", "preco": 50.0, "estoque": 3, "status": "active"}
    fatos = {"midia_cadastrada": True, "destino_produto_especifico": True, "cookie_clique_visivel": True,
             "usa_shortener": False, "compara_com_outro_produto": False, "simula_canal_oficial": False,
             "midia_paga": False, "informacoes_constam_anuncio": True}
    with patch("MKTFLOW.orchestrator.consultar_api_publica_mercado_livre", return_value=fake_ml):
        r = run_pipeline("https://www.mercadolivre.com.br/p/MLB888001003?matt_word=x", fatos=fatos)
        assert r["status_validacao"] == "PASS"
    with patch("MKTFLOW.orchestrator.consultar_api_publica_mercado_livre", return_value=fake_ml):
        with patch("MKTFLOW.orchestrator.extrair_item_id", return_value="MLB888001003"):
            r = run_pipeline("https://mercadolivre.com/sec/abc?matt_word=x")
            assert r["link_id"]
    with patch("MKTFLOW.orchestrator.consultar_api_publica_mercado_livre", return_value=fake_ml), \
         patch("MKTFLOW.orchestrator.publicar_no_wordpress", return_value={"post_id": 1, "link": "https://w/1", "status": "draft"}) as mp, \
         patch("MKTFLOW.orchestrator.WPConfig.is_configured", return_value=True):
        from MKTFLOW.wp_publisher import WPConfig
        r = run_pipeline("https://www.mercadolivre.com.br/p/MLB888001003?matt_word=x", fatos=fatos, publicar=True,
                         wp_config=WPConfig("https://w", "u", "p"))
        assert mp.called
