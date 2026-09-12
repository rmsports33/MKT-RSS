"""
Testes P0.5 — ROI com dedução
pytest tests/test_roi_p0.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.roi import calcular_roi_afiliado

def test_roi_sem_deducao():
    r = calcular_roi_afiliado(cpc=0.5, cliques=1000, taxa_conversao=2.0, valor_medio_produto=100.0, comissao_pct=10.0, deducao_pct=0.0)
    # custo 500, vendas 20, bruta 200, liquida 200, lucro -300, roi -60%
    assert r["custo_ads_brl"] == 500.0
    assert r["vendas_estimadas"] == 20.0
    assert r["comissao_bruta_brl"] == 200.0
    assert r["comissao_liquida_brl"] == 200.0
    assert r["lucro_liquido_brl"] == -300.0
    assert r["roi_pct"] == -60.0

def test_roi_com_deducao():
    r = calcular_roi_afiliado(cpc=0.5, cliques=1000, taxa_conversao=2.0, valor_medio_produto=100.0, comissao_pct=10.0, deducao_pct=10.0)
    # bruta 200, liquida 180 (10% dedução), lucro -320
    assert r["comissao_liquida_brl"] == 180.0
    assert r["lucro_liquido_brl"] == -320.0
    assert r["roi_pct"] == -64.0

def test_roi_organico_sem_custo():
    r = calcular_roi_afiliado(cpc=0.0, cliques=1000, taxa_conversao=2.0, valor_medio_produto=100.0, comissao_pct=10.0)
    assert r["custo_ads_brl"] == 0.0
    assert r["roi_pct"] == 0.0  # evita divisão por zero
    assert r["lucro_liquido_brl"] == 200.0

def test_roi_zero_cliques():
    r = calcular_roi_afiliado(cpc=1.0, cliques=0, taxa_conversao=5.0, valor_medio_produto=200.0, comissao_pct=5.0)
    assert r["vendas_estimadas"] == 0.0
    assert r["comissao_bruta_brl"] == 0.0

def test_deducao_100pct():
    r = calcular_roi_afiliado(cpc=0.1, cliques=100, taxa_conversao=10.0, valor_medio_produto=50.0, comissao_pct=20.0, deducao_pct=100.0)
    assert r["comissao_liquida_brl"] == 0.0

if __name__ == "__main__":
    for n, fn in list(globals().items()):
        if n.startswith("test_"):
            fn()
            print(f"[OK] {n}")
    print("Todos P0.5 passaram")
