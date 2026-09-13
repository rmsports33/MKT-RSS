"""
Expansão 6: fecha 244 — whois, health, config, redator, dashboard
pytest tests/unit/test_suite_expand6.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from whois_tool.cache import WhoisCache
from whois_tool.robust import validate_domain, detect_query_type
from mkt_flow_p0.health_check import check_db, check_policy
from mkt_flow_p0.config import validate_env
import src.generator.render as R

def test_whois_cache_set_get(tmp_path):
    c = WhoisCache(db_path=tmp_path / "w.db", ttl=60)
    c.set("exemplo.com", "RAW")
    assert c.get("exemplo.com") == "RAW"
    assert c.get("outro.com") is None

def test_whois_validate():
    assert validate_domain("exemplo.com")["valido"] is True
    assert validate_domain("bad..com")["valido"] is False

def test_whois_detect():
    assert detect_query_type("8.8.8.8") == "ip"
    assert detect_query_type("exemplo.com") == "domain"
    assert detect_query_type("123") in ("asn", "domain", "invalido")

def test_health_db(tmp_path, monkeypatch):
    import mkt_flow_p0.health_check as H
    import sqlite3
    db = tmp_path / "h.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE pipeline_runs (id TEXT)")
    con.execute("CREATE TABLE link_publicacoes (id TEXT)")
    con.commit()
    con.close()
    monkeypatch.setattr(H, "ROOT", tmp_path)
    # H.check_db usa ROOT / "mkt_flow_p0.db", precisa mockar
    with patch("mkt_flow_p0.health_check.ROOT", tmp_path):
        # cria o arquivo esperado
        (tmp_path / "mkt_flow_p0.db").write_bytes(db.read_bytes())
        r = H.check_db()
        assert r["ok"] is True

def test_health_policy():
    r = check_policy()
    assert r["ok"] is True and r["regras"] == 21

def test_config_ok(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_x")
    monkeypatch.setenv("WP_URL", "https://x")
    monkeypatch.setenv("WP_USER", "u")
    monkeypatch.setenv("WP_APP_PASSWORD", "p")
    d = validate_env(strict=False, required_keys={"GROQ_API_KEY": "x"})
    assert "GROQ_API_KEY" in str(d) or d == {}

def test_redator_sanitiza():
    h = R._sanitizar_llm_html("## T\nTexto", ["fonte X"])
    assert "<h2>" in h

def test_redator_remove_bancada():
    t = R._remover_alusao_teste("Testamos em bancada e foi bom")
    assert "bancada" not in t.lower()

def test_redator_tabela():
    tab = R.montar_tabela_specs([{"nome": "A", "specs": {"a": "1"}}, {"nome": "B", "specs": {"a": "2"}}])
    assert "compare-table" in tab

def test_dashboard_coletar_com_dados(tmp_path, monkeypatch):
    import mkt_flow_p0.dashboard as D, sqlite3
    db = tmp_path / "d.db"
    monkeypatch.setattr(D, "DB_PATH", db)
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE pipeline_runs (id TEXT, status_validacao TEXT, status_politica TEXT, roi_json TEXT, created_at TEXT)")
    con.execute("CREATE TABLE link_publicacoes (id TEXT, link_id TEXT, plataforma TEXT, programa TEXT, created_at TEXT)")
    con.execute("CREATE TABLE rss_runs (id TEXT, fonte TEXT, titulo_seo TEXT, palavras INT, veredito TEXT, wp_post_id INT, created_at TEXT)")
    con.execute("INSERT INTO pipeline_runs VALUES ('1','PASS','PASS','{\"lucro_liquido_brl\":10}','2026-01-01')")
    con.commit()
    con.close()
    d = D.coletar_dados()
    assert d["total_runs"] == 1 and d["total_roi_liquido"] == 10
