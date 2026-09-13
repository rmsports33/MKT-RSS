"""
Expansão 4: health_check, config, whois, backup, pipeline_p0, redator
pytest tests/unit/test_suite_expand4.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import mkt_flow_p0.health_check as H
import mkt_flow_p0.config as CFG
from whois_tool.robust import sanitize_and_normalize, validate_domain
from whois_tool.parser import parse_whois

def test_health_check_env_ok(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    monkeypatch.setenv("WP_URL", "https://site.com")
    monkeypatch.setenv("WP_USER", "u")
    monkeypatch.setenv("WP_APP_PASSWORD", "p")
    r = H.check_env()
    assert r["groq_ok"] is True and r["wp_ok"] is True

def test_health_check_env_falta(monkeypatch):
    # isola .env: não carrega do disco
    with patch("dotenv.load_dotenv", return_value=None):
        for k in ["GROQ_API_KEY","WP_URL","WP_USER","WP_APP_PASSWORD"]:
            monkeypatch.delenv(k, raising=False)
        r = H.check_env()
        assert r["groq_ok"] is False

def test_config_validate_strict_falha(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    try:
        CFG.validate_env(strict=True, required_keys={"GROQ_API_KEY": "x"})
        assert False
    except RuntimeError as e:
        assert "GROQ_API_KEY" in str(e)

def test_whois_sanitize():
    assert sanitize_and_normalize("https://Exemplo.com/caminho") == "exemplo.com"
    assert sanitize_and_normalize("  EXEMPLO.COM  ") == "exemplo.com"

def test_whois_validate():
    assert validate_domain("exemplo.com")["valido"] is True
    assert validate_domain("not a domain")["valido"] is False

def test_whois_parse():
    raw = "Domain Name: EXEMPLO.COM\nRegistrar: Test\nCreation Date: 2020-01-01\n"
    p = parse_whois(raw)
    assert p["domain"] == "exemplo.com"
    assert p["registrar"] == "Test"

def test_backup_coletar_vazio(tmp_path):
    from scripts.backup_drive import coletar_arquivos
    assert coletar_arquivos(tmp_path) == []

def test_pipeline_p0_extrair():
    import pipeline_p0
    assert pipeline_p0.extrair_item_id("https://x/MLB123?matt_word=a") == "MLB123"
    assert pipeline_p0.extrair_item_id("https://x/sem") == ""

def test_pipeline_p0_init(tmp_path, monkeypatch):
    import pipeline_p0 as P0
    monkeypatch.setattr(P0, "DB_PATH", tmp_path / "p.db")
    P0.init_db()
    import sqlite3
    con = sqlite3.connect(tmp_path / "p.db")
    assert "pipeline_runs" in [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

def test_redator_prompt():
    from src.generator.prompt import montar_system_prompt
    s = montar_system_prompt("celular")
    assert "celular" in s.lower() and "não informado" in s

def test_redator_evergreen_fallback(monkeypatch):
    import src.evergreen as E
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with patch.object(E, "_try_call", side_effect=Exception("down")):
        r = E.gerar_texto("s", "u")
        assert "erro" in r

def test_format_truncar_borda():
    from mkt_flow_p0.format import truncar_palavras
    assert truncar_palavras("a b c d e f g h i j k l m n o p", 5) in ("a b", "a")

def test_format_sanitizar():
    from mkt_flow_p0.format import sanitizar_url
    assert sanitizar_url(" https://x.com/a\x00 ") == "https://x.com/a"

def test_alerts_check_all():
    from mkt_flow_p0.alerts import check_all
    with patch("mkt_flow_p0.alerts._check_url_head", return_value={"url": "u", "http_code": 200, "ok": True, "elapsed_ms": 1}):
        r = check_all([{"url": "https://x"}])
        assert r["total"] == 1

def test_dashboard_coletar(tmp_path, monkeypatch):
    import mkt_flow_p0.dashboard as D
    monkeypatch.setattr(D, "DB_PATH", tmp_path / "d2.db")
    d = D.coletar_dados()
    assert "total_runs" in d and "rss_total" in d
