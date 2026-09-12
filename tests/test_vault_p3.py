"""
Testes P3 — vault + compat programa x plataforma
pytest tests/test_vault_p3.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import mkt_flow_p0.vault as V


def test_registrar_e_listar(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "DB_PATH", tmp_path / "v.db")
    r = V.registrar_identidade("instagram", "@conexotech", nicho="tech")
    assert r["identity_id"].startswith("identity_instagram_")
    assert len(V.listar_identidades("instagram")) == 1


def test_limites_conhecidos():
    assert V.get_platform_limits("instagram")["max_posts_per_day"] == 5
    assert V.get_platform_limits("wordpress")["link_no_corpo"] is True
