"""
Testes legados — MKTFLOW.orchestrator + db (mocks)
pytest tests/test_orchestrator.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent.parent / "MKTFLOW"))
sys.path.insert(0, str(Path(__file__).parent.parent))
from MKTFLOW.orchestrator import run_pipeline
from MKTFLOW.db import get_db

FAKE_ML = {"titulo": "P", "preco": 100.0, "estoque": 5, "status": "active"}
FATOS_OK = {"midia_cadastrada": True, "destino_produto_especifico": True, "cookie_clique_visivel": True,
            "usa_shortener": False, "compara_com_outro_produto": False, "simula_canal_oficial": False,
            "midia_paga": False, "informacoes_constam_anuncio": True}


def test_allow_pass_completo():
    with patch("MKTFLOW.orchestrator.consultar_api_publica_mercado_livre", return_value=FAKE_ML):
        r = run_pipeline("https://www.mercadolivre.com.br/p/MLB999001001?matt_word=x", fatos=FATOS_OK)
        assert r["decision"] == "ALLOW" and r["status_validacao"] == "PASS"


def test_block_sem_tag():
    with patch("MKTFLOW.orchestrator.consultar_api_publica_mercado_livre", return_value=FAKE_ML):
        r = run_pipeline("https://www.mercadolivre.com.br/p/MLB999001002")
        assert r["decision"] == "BLOCK"


def test_block_policy_fail():
    with patch("MKTFLOW.orchestrator.consultar_api_publica_mercado_livre", return_value=FAKE_ML), \
         patch("MKTFLOW.orchestrator.avaliar_politica",
               return_value={"status_politica": "FAIL", "programa": "mercado_livre",
                             "regras": [{"regra_id": "ML-X", "evidencia": "e"}]}):
        r = run_pipeline("https://www.mercadolivre.com.br/p/MLB999001003?matt_word=x")
        assert r["decision"] == "BLOCK"


def test_block_unknown_sem_publish():
    with patch("MKTFLOW.orchestrator.consultar_api_publica_mercado_livre", return_value=FAKE_ML):
        r = run_pipeline("https://shopee.com.br/produto-x")
        assert r["decision"] == "BLOCK" and r["wp"] == {}


def test_persiste_affiliate_runs():
    with patch("MKTFLOW.orchestrator.consultar_api_publica_mercado_livre", return_value=FAKE_ML):
        r = run_pipeline("https://www.mercadolivre.com.br/p/MLB999001004?matt_word=x")
        con = get_db()
        row = con.execute("SELECT status FROM affiliate_runs WHERE id=?", (r["link_id"],)).fetchone()
        con.close()
        assert row and row["status"] == "PASS"
