"""
Testes P0 — cloud_db Turso HTTP + roteamento do dedup (tudo mockado)
pytest tests/test_cloud_db_p0.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0 import cloud_db as C
import mkt_flow_p0.rss_ingestor as R


def _resp_ok(rows=(("x",),)):
    m = MagicMock()
    m.status_code = 200
    m.json.return_value = {"results": [{"type": "ok", "response": {"type": "execute", "result": {
        "cols": [{"name": "c"}], "rows": [[{"type": "text", "value": v} for v in linha] for linha in rows],
        "affected_row_count": 1}}}]}
    return m


def test_desligado_sem_env(monkeypatch):
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    assert C.turso_enabled() is False


def test_ligado_com_env(monkeypatch):
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://db-org.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "tok")
    assert C.turso_enabled() is True
    assert C._base_url() == "https://db-org.turso.io/v2/pipeline"


def test_execute_ok_parse(monkeypatch):
    monkeypatch.setenv("TURSO_DATABASE_URL", "https://db.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "tok")
    with patch("mkt_flow_p0.cloud_db.requests.post", return_value=_resp_ok((("abc",),))) as mp:
        r = C.turso_execute("SELECT 1 FROM rss_vistos WHERE id=?", ("abc",))
        assert r["rows"] == [["abc"]]
        corpo = mp.call_args.kwargs["json"]
        assert corpo["requests"][0]["stmt"]["args"] == [{"type": "text", "value": "abc"}]
        assert corpo["requests"][-1] == {"type": "close"}


def test_execute_401_orienta():
    m = MagicMock()
    m.status_code = 401
    with patch("mkt_flow_p0.cloud_db.requests.post", return_value=m):
        assert "401" in C.turso_execute("SELECT 1")["erro"]


def test_execute_erro_sql():
    m = MagicMock()
    m.status_code = 200
    m.json.return_value = {"results": [{"type": "error", "error": {"message": "no such table"}}]}
    with patch("mkt_flow_p0.cloud_db.requests.post", return_value=m):
        assert "no such table" in C.turso_execute("SELECT 1")["erro"]


def test_dedup_usa_turso_quando_ligado(monkeypatch):
    monkeypatch.setenv("TURSO_DATABASE_URL", "https://db.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "tok")
    chamadas = []

    def fake_execute(sql, args=()):
        chamadas.append(sql)
        if sql.startswith("SELECT 1"):
            return {"cols": [], "rows": []}
        if "titulo_norm" in sql:
            return {"cols": ["titulo_norm"], "rows": []}
        return {"cols": [], "rows": [], "affected": 1}

    with patch.object(R, "turso_execute", side_effect=fake_execute):
        assert R.item_ja_visto("https://e.com/nova", "Título inédito xyz") is False
        R.marcar_visto("blog", "https://e.com/nova", "Título inédito xyz")
        assert any("INSERT OR IGNORE" in s for s in chamadas)


def test_dedup_turso_encontra_url(monkeypatch):
    monkeypatch.setenv("TURSO_DATABASE_URL", "https://db.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "tok")

    def fake_execute(sql, args=()):
        if sql.startswith("SELECT 1"):
            return {"cols": [], "rows": [[1]]}
        return {"cols": [], "rows": []}

    with patch.object(R, "turso_execute", side_effect=fake_execute):
        assert R.item_ja_visto("https://e.com/ja-vista", "Qualquer") is True
