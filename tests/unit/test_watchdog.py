"""
Testes — watchdog (offline, API mockada)
pytest tests/unit/test_watchdog.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.watchdog import ultimo_run, disparar


def _resp_runs(horas_atras=2, conclusion="success"):
    from datetime import datetime, timezone, timedelta
    dt = (datetime.now(timezone.utc) - timedelta(hours=horas_atras)).isoformat().replace("+00:00", "Z")
    m = MagicMock()
    m.status_code = 200
    m.json.return_value = {"workflow_runs": [{"conclusion": conclusion, "updated_at": dt, "html_url": "https://x"}]}
    m.raise_for_status.return_value = None
    return m


def test_ultimo_run_ok():
    with patch("scripts.watchdog.requests.get", return_value=_resp_runs(2, "success")):
        r = ultimo_run("o/r", "tok")
        assert r["conclusion"] == "success"


def test_disparar_ok():
    m = MagicMock()
    m.status_code = 204
    with patch("scripts.watchdog.requests.post", return_value=m):
        assert disparar("o/r", "tok")["ok"] is True


def test_disparar_401():
    m = MagicMock()
    m.status_code = 401
    m.text = "Bad credentials"
    with patch("scripts.watchdog.requests.post", return_value=m):
        r = disparar("o/r", "tok")
        assert r["ok"] is False and r["status"] == 401
