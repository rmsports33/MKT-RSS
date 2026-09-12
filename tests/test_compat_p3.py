"""
Testes P3 — compatibilidade programa x plataforma no agendamento
pytest tests/test_compat_p3.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import mkt_flow_p0.scheduler as S
import mkt_flow_p0.vault as V


def test_agendar_com_programa_ok(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "DB_PATH", tmp_path / "c.db")
    monkeypatch.setattr(V, "DB_PATH", tmp_path / "c.db")
    r = V.agendar_com_programa("mercado_livre", "tiktok", "conteudo-1")
    assert r["compativel"] is True and r["status"] == "agendado"


def test_compat_mercadolivre_tiktok():
    g = V.checar_compatibilidade("mercado_livre", "tiktok")
    assert g["compativel"] is True


def test_scheduler_usa_vault_limits():
    lim = S.get_platform_limits("instagram")
    assert lim["max_posts_per_day"] == V.get_platform_limits("instagram")["max_posts_per_day"]


def test_shopee_wordpress_bloqueado(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "DB_PATH", tmp_path / "c2.db")
    monkeypatch.setattr(V, "DB_PATH", tmp_path / "c2.db")
    r = V.agendar_com_programa("shopee", "wordpress", "conteudo-x")
    assert r["compativel"] is False and "erro" in r
