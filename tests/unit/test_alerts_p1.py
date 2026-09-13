"""
Testes P1 — alerts (quebrados + estoque, mocks)
pytest tests/test_alerts_p1.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.alerts import checar_links_quebrados, checar_estoque, check_link


def _head_ok(url, timeout=8):
    return {"url": url, "http_code": 200, "ok": True, "elapsed_ms": 50}


def test_checar_links_quebrados_ok():
    with patch("mkt_flow_p0.alerts._check_url_head", side_effect=_head_ok):
        assert checar_links_quebrados(["https://a.com"]) == []


def test_checar_links_404():
    bad = {"url": "https://a.com/x", "http_code": 404, "ok": False, "elapsed_ms": 100}
    with patch("mkt_flow_p0.alerts._check_url_head", return_value=bad):
        crit = checar_links_quebrados(["https://a.com/x"])
        assert len(crit) == 1 and crit[0]["url"].endswith("/x")


def test_checar_estoque_mock():
    with patch("mkt_flow_p0.alerts._check_url_head", side_effect=_head_ok), \
         patch("mkt_flow_p0.api_ml.consultar_api_publica_mercado_livre",
               return_value={"titulo": "P", "preco": 10.0, "estoque": 0, "status": "active"}):
        r = check_link("https://ml.com/p/MLB1", item_id="MLB1")
        assert r["severidade"] == "HIGH" and r["motivo"] == "sem_estoque"
