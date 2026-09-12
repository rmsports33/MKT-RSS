"""
Testes legados — MKTFLOW.alerts (mocks)
pytest tests/test_alerts.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent.parent / "MKTFLOW"))
sys.path.insert(0, str(Path(__file__).parent.parent))
from MKTFLOW.alerts import check_link, check_all, _check_url_head
from MKTFLOW.orchestrator import run_pipeline


def test_check_url_head_mock():
    with patch("MKTFLOW.alerts.requests.head") as mh:
        mh.return_value.status_code = 200
        r = _check_url_head("https://a.com")
        assert r["ok"] is True and r["http_code"] == 200


def test_check_url_head_404():
    with patch("MKTFLOW.alerts.requests.head") as mh:
        mh.return_value.status_code = 404
        assert _check_url_head("https://a.com/x")["ok"] is False


def test_check_link_critical_404():
    with patch("MKTFLOW.alerts._check_url_head",
               return_value={"url": "u", "http_code": 404, "ok": False, "elapsed_ms": 100}):
        r = check_link("https://a.com/x")
        assert r["severidade"] == "CRITICAL"


def test_check_link_out_of_stock():
    fake_stock0 = {"titulo": "P", "preco": 10.0, "estoque": 0, "status": "active"}
    with patch("MKTFLOW.alerts._check_url_head",
               return_value={"url": "u", "http_code": 200, "ok": True, "elapsed_ms": 80}), \
         patch("MKTFLOW.alerts.consultar_api_publica_mercado_livre", return_value=fake_stock0):
        r = check_link("https://ml.com/p/MLB1", item_id="MLB1")
        assert r["severidade"] == "HIGH"


def test_check_link_ok():
    fake_ml = {"titulo": "P", "preco": 10.0, "estoque": 5, "status": "active"}
    with patch("MKTFLOW.alerts._check_url_head",
               return_value={"url": "u", "http_code": 200, "ok": True, "elapsed_ms": 50}), \
         patch("MKTFLOW.alerts.consultar_api_publica_mercado_livre", return_value=fake_ml):
        assert check_link("https://ml.com/p/MLB1", item_id="MLB1")["severidade"] == "OK"


def test_check_all():
    fake_ml = {"titulo": "P", "preco": 10.0, "estoque": 5, "status": "active"}
    with patch("MKTFLOW.orchestrator.consultar_api_publica_mercado_livre", return_value=fake_ml):
        r = check_all([{"url": "https://a.com"}, {"url": "https://b.com"}])
        assert r["total"] == 2
