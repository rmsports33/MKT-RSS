"""
Testes P1 — dashboard (coleta sem DB quebrado)
pytest tests/test_dashboard_p1.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.dashboard import coletar_dados, gerar_html


def test_coletar_dados_estrutura(tmp_path, monkeypatch):
    import mkt_flow_p0.dashboard as D
    monkeypatch.setattr(D, "DB_PATH", tmp_path / "dash.db")
    d = coletar_dados()
    assert d["total_runs"] == 0 and d["total_pubs"] == 0
    assert "runs" in d and "pubs" in d


def test_gerar_html_vazio():
    h = gerar_html({"total_runs": 0, "total_pubs": 0, "valid_pass": 0, "policy_pass": 0,
                    "by_platform": {}, "by_program": {}, "runs": [], "pubs": [], "costs": [],
                    "total_roi_liquido": 0, "total_custo": 0, "cost_total": 0})
    assert "MKT Flow" in h and "Nenhum run" in h
