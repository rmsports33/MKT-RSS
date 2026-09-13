"""
Testes P1 — scheduler (agenda, vencidos, retry)
pytest tests/test_scheduler_p1.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import mkt_flow_p0.scheduler as S


def test_agendar_e_vencidos(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "DB_PATH", tmp_path / "s.db")
    r = S.schedule_post("c1", "wordpress", "2000-01-01T00:00:00")
    assert r["status"] == "agendado"
    due = S.get_due_posts("2026-01-01T00:00:00")
    assert any(d["content_id"] == "c1" for d in due)
    assert S.mark_published(r["schedule_id"]) is True
    assert S.get_due_posts("2026-01-01T00:00:00") == []


def test_retry_backoff(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "DB_PATH", tmp_path / "s2.db")
    r = S.schedule_post("c2", "instagram", "2000-01-01T00:00:00")
    f1 = S.mark_failed(r["schedule_id"])
    assert f1["status"] == "agendado" and f1["tentativas"] == 1
