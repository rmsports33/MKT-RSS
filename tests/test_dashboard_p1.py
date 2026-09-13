"""
Testes P1 — dashboard (coleta sem DB quebrado)
pytest tests/test_dashboard_p1.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.dashboard import coletar_dados, gerar_html


def test_coletar_dados_estrutura(tmp_path, monkeypatch):
    import mkt_flow_p0.dashboard as D
    monkeypatch.setattr(D, "DB_PATH", tmp_path / "dash.db")
    d = coletar_dados()
    assert d["total_runs"] == 0 and d["total_pubs"] == 0
    assert "runs" in d and "pubs" in d


def test_gerar_html_vazio():
    h = gerar_html({"total_runs": 0, "total_pubs": 0, "valid_pass": 0, "policy_pass": 0,
                    "by_platform": {}, "by_program": {}, "runs": [], "pubs": [], "costs": [],
                    "total_roi_liquido": 0, "total_custo": 0, "cost_total": 0})
    assert "MKT Flow" in h and "Nenhum run" in h


def test_coletar_com_rss(tmp_path, monkeypatch):
    import sqlite3
    import mkt_flow_p0.dashboard as D
    db = tmp_path / "dash2.db"
    monkeypatch.setattr(D, "DB_PATH", db)
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE pipeline_runs (id TEXT, status_validacao TEXT, status_politica TEXT, roi_json TEXT)")
    con.execute("CREATE TABLE link_publicacoes (id TEXT, link_id TEXT, plataforma TEXT, programa TEXT)")
    con.execute("CREATE TABLE rss_runs (id TEXT, fonte TEXT, titulo_seo TEXT, palavras INT, veredito TEXT, wp_post_id INT, created_at TEXT)")
    con.execute("INSERT INTO rss_runs VALUES ('r1','blog','Titulo A',500,'APROVADO',9,'2026-01-01')")
    con.execute("INSERT INTO rss_runs VALUES ('r2','blog','Titulo B',0,'BLOQUEADO',NULL,'2026-01-02')")
    con.commit()
    con.close()
    d = coletar_dados()
    assert d["rss_total"] == 2 and d["rss_publicados"] == 1 and d["rss_bloqueados"] == 1
    h = gerar_html(d)
    assert "Titulo A" in h and "RSS publicados" in h
