"""
Testes P1 — link tracker (registro e contagem isolados)
pytest tests/test_link_tracker_p1.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import mkt_flow_p0.link_tracker as T


def test_registrar_e_listar(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "DB_PATH", tmp_path / "t.db")
    pid = T.registrar_publicacao("abc123", "https://ml.com/p/1", "wordpress", "mercado_livre", "https://site.com/p/1", "PASS")
    assert pid
    pubs = T.listar_publicacoes("abc123")
    assert len(pubs) == 1 and pubs[0]["url_publicacao"].endswith("/p/1")


def test_contar_por_plataforma(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "DB_PATH", tmp_path / "t2.db")
    T.registrar_publicacao("a", "u1", "wordpress", "p", "url1", "PASS")
    T.registrar_publicacao("b", "u2", "wordpress", "p", "url2", "PASS")
    assert T.contar_por_plataforma()["wordpress"] == 2
