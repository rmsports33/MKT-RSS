"""
Testes P0 — wp_publisher (gate PASS + draft)
pytest tests/test_wp_publisher_p0.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.wp_publisher import publicar_no_wordpress


def _ok(post_id=1, status="draft"):
    m = MagicMock()
    m.status_code = 201
    m.json.return_value = {"id": post_id, "link": f"https://site.com/?p={post_id}", "status": status}
    return m


def test_bloqueia_publish_sem_pass():
    r = publicar_no_wordpress("T", "<p>x</p>", "UNKNOWN", "https://site.com", "u", "p", status_desejado="publish")
    assert "erro" in r and "bloqueada" in r["erro"].lower()


def test_draft_without_reviewed_package_is_blocked():
    with patch("mkt_flow_p0.wp_publisher.requests.post", return_value=_ok()) as mp:
        r = publicar_no_wordpress("T", "<p>x</p>", "UNKNOWN", "https://site.com", "u", "p")
        assert "erro" in r
        mp.assert_not_called()


def test_pass_alone_cannot_publish():
    with patch("mkt_flow_p0.wp_publisher.requests.post", return_value=_ok(2, "publish")) as mp:
        r = publicar_no_wordpress("T", "<p>x</p>", "PASS", "https://site.com", "u", "p", status_desejado="publish")
        assert "erro" in r
        mp.assert_not_called()


def test_sem_credencial_erro():
    assert "erro" in publicar_no_wordpress("T", "<p>x</p>", "PASS", "", "", "")

