"""
Testes legados — MKTFLOW.roi_calculator
pytest tests/test_roi_calculator.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "MKTFLOW"))
sys.path.insert(0, str(Path(__file__).parent.parent))
from MKTFLOW.roi_calculator import calcular_roi_afiliado, calcular_roi_por_categoria


def test_basico():
    r = calcular_roi_afiliado(0.5, 1000, 2.0, 100.0, 10.0)
    assert r["roi_pct"] == -60.0 and r["lucro_liquido_brl"] == -300.0


def test_por_categoria():
    r = calcular_roi_por_categoria("eletronicos", 0.0, 100, 5.0, 200.0, 8.0)
    assert r["categoria"] == "eletronicos" and r["roi_pct"] == 0.0
    assert r["comissao_bruta_brl"] == 80.0
