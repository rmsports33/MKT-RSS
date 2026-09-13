"""
Testes legados — MKTFLOW.scheduler
pytest tests/test_scheduler.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "MKTFLOW"))
sys.path.insert(0, str(Path(__file__).parent.parent))
from MKTFLOW.scheduler import schedule_post, get_calendar_view, get_due_posts, mark_published, mark_failed, list_schedules, clear_schedules, get_platform_limits


def test_ciclo():
    clear_schedules()
    r = schedule_post("c1", "wordpress", "2000-01-01T00:00:00")
    assert r["status"] == "agendado"
    assert any(d["content_id"] == "c1" for d in get_due_posts("2026-01-01T00:00:00"))
    assert mark_published(r["schedule_id"]) is True
    clear_schedules()


def test_falha_reagenda():
    clear_schedules()
    r = schedule_post("c2", "instagram", "2000-01-01T00:00:00")
    f = mark_failed(r["schedule_id"])
    assert f["status"] == "agendado"
    clear_schedules()


def test_limites_e_calendario():
    assert get_platform_limits("instagram")["max_posts_per_day"] == 5
    clear_schedules()
    schedule_post("c3", "wordpress", "2026-05-01T10:00:00")
    cal = get_calendar_view("2026-05-01T00:00:00", "2026-05-02T00:00:00")
    assert cal["total"] >= 1
    clear_schedules()
    assert list_schedules() == []
