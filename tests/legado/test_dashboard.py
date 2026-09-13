"""
Testes legados — MKTFLOW.dashboard + orchestrator (mocks)
pytest tests/test_dashboard.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent.parent / "MKTFLOW"))
sys.path.insert(0, str(Path(__file__).parent.parent))
from MKTFLOW.dashboard import get_consolidated_metrics, get_product_performance_matrix, generate_html_dashboard
from MKTFLOW.orchestrator import run_pipeline


def test_metrics_agrupado():
    m = get_consolidated_metrics()
    assert "total_runs" in m and "por_plataforma" in m
    assert generate_html_dashboard(m).startswith("<!DOCTYPE html>")


def test_metrics_produto():
    fake_ml = {"titulo": "P", "preco": 10.0, "estoque": 5, "status": "active"}
    with patch("MKTFLOW.orchestrator.consultar_api_publica_mercado_livre", return_value=fake_ml):
        r = run_pipeline("https://x.com", programa="mercado_livre")
        assert r["decision"] == "BLOCK"
    mx = get_product_performance_matrix()
    assert "matriz" in mx
