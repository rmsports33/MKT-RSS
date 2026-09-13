"""
Testes legados — MKTFLOW.wp_publisher (gate + post mockado)
pytest tests/test_wp_publisher.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests
sys.path.insert(0, str(Path(__file__).parent.parent / "MKTFLOW"))
sys.path.insert(0, str(Path(__file__).parent.parent))
from MKTFLOW.wp_publisher import WPConfig, publicar_no_wordpress, _check_gate


def _cfg():
    return WPConfig("https://site.com", "u", "p")


def _ok(status="draft"):
    m = MagicMock()
    m.status_code = 201
    m.json.return_value = {"id": 7, "link": "https://site.com/?p=7", "status": status}
    return m


def test_gate():
    assert _check_gate("PASS", "publish") == "publish"
    assert _check_gate("UNKNOWN", "publish") == "draft"


def test_publica_draft():
    with patch("MKTFLOW.wp_publisher.requests.post", return_value=_ok()) as mp:
        r = publicar_no_wordpress(_cfg(), "T", "<p>x</p>", "UNKNOWN")
        assert r["status"] == "draft" and mp.called


def test_bloqueia_publish():
    with patch("MKTFLOW.wp_publisher.requests.post") as mp:
        r = publicar_no_wordpress(_cfg(), "T", "<p>x</p>", "FAIL", status_desejado="publish")
        assert "erro" in r and not mp.called


def test_timeout():
    with patch("MKTFLOW.wp_publisher.requests.post", side_effect=requests.exceptions.Timeout("timed out")):
        assert "timeout" in publicar_no_wordpress(_cfg(), "T", "<p>x</p>", "PASS")["erro"]


def test_sem_config():
    assert "erro" in publicar_no_wordpress(WPConfig(), "T", "<p>x</p>", "PASS")
