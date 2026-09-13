"""
Expansão 3: pipeline_rss, dashboard, rss_ingestor edge, rewriter gates
pytest tests/unit/test_suite_expand3.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import pipeline_rss as P
import mkt_flow_p0.rss_ingestor as R
import mkt_flow_p0.dashboard as D
from mkt_flow_p0.rewriter import gerar_slug, _parse_json_resposta

def test_slug_vazio():
    assert gerar_slug("") == "materia"
    assert gerar_slug("A B!") == "a-b"

def test_parse_json_cerca():
    assert _parse_json_resposta('```json\n{"a":1}\n```')["a"] == 1

def test_rss_fetch_sem_feedparser(monkeypatch):
    import mkt_flow_p0.rss_ingestor as R2
    monkeypatch.setattr(R2, "_HAS_FEEDPARSER", False)
    assert "erro" in R2.fetch_feed("https://x")

def test_rss_dedup_idempotente(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "DB_PATH", tmp_path / "d.db")
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    R.marcar_visto("f", "https://x/a", "Titulo A")
    assert R.item_ja_visto("https://x/a", "Titulo A") is True
    # outro titulo deve ser falso (não similar)
    assert R.item_ja_visto("https://x/b", "Titulo Completamente Diferente XYZ") is False

def test_extractor_url_invalida():
    from mkt_flow_p0.extractor import extrair_conteudo
    assert "erro" in extrair_conteudo("nota-url")

def test_pipeline_init_db_migracao(tmp_path, monkeypatch):
    import sqlite3
    monkeypatch.setattr(P, "DB_PATH", tmp_path / "p.db")
    P.init_db()
    con = sqlite3.connect(tmp_path / "p.db")
    cols = [r[1] for r in con.execute("PRAGMA table_info(rss_runs)").fetchall()]
    assert "custo_usd" in cols

def test_pipeline_publicar_indice_vazio(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "DB_PATH", tmp_path / "e.db")
    P.init_db()
    monkeypatch.chdir(tmp_path)
    r = P.publicar_indice()
    assert "aviso" in r or "arquivos" in r

def test_pipeline_processar_bloqueado_off_topic():
    with patch("mkt_flow_p0.content_filter.filtrar_por_tema", return_value={"veredito": "BLOQUEADO", "motivo": "off_topic"}):
        assert P.processar_item({"titulo": "lua", "resumo": "", "link": "u"})["acao"] == "bloqueado"

def test_dashboard_coletar_vazio(tmp_path, monkeypatch):
    monkeypatch.setattr(D, "DB_PATH", tmp_path / "dash.db")
    d = D.coletar_dados()
    assert d["total_runs"] == 0
    assert "rss_total" in d

def test_dashboard_html_vazio():
    h = D.gerar_html({"total_runs":0,"total_pubs":0,"valid_pass":0,"policy_pass":0,"by_platform":{},"by_program":{},"runs":[],"pubs":[],"costs":[],"total_roi_liquido":0,"total_custo":0,"cost_total":0,"rss_total":0,"rss_publicados":0,"rss_bloqueados":0,"rss":[],"affiliate_runs_classico":0})
    assert "MKT Flow" in h

def test_validator_shopee_unknown():
    from mkt_flow_p0.validator import validar_link_afiliado
    assert validar_link_afiliado("https://shopee.com.br/x", resolver_redirect=False)["status_validacao"] == "UNKNOWN"

def test_policy_unknown_programa():
    from mkt_flow_p0.policy_engine import avaliar_politica
    assert avaliar_politica("desconhecido", {})["status_politica"] == "UNKNOWN"

def test_roi_zero_custo():
    from mkt_flow_p0.roi import calcular_roi_afiliado
    r = calcular_roi_afiliado(0, 100, 5.0, 100.0, 10.0)
    assert r["roi_pct"] == 0.0

def test_landing_gate():
    from mkt_flow_p0.landing import gerar_template_landing_page
    assert "BLOQUEADO" in gerar_template_landing_page("P", "https://x", "10", status_validacao="FAIL")
    assert "Ir para a Loja" in gerar_template_landing_page("P", "https://x", "10", status_validacao="PASS")

def test_format_xss():
    from mkt_flow_p0.format import markdown_para_html
    assert "<script>" not in markdown_para_html('<script>alert(1)</script>')

def test_keyword_empty():
    from mkt_flow_p0.keyword_research import sugerir_keywords_review
    assert sugerir_keywords_review("", limit=3) == []

def test_cloud_batch_erro(monkeypatch):
    import mkt_flow_p0.cloud_db as C2
    monkeypatch.setenv("TURSO_DATABASE_URL", "https://db.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "tok")
    m = MagicMock()
    m.status_code = 200
    m.json.return_value = {"results": [{"type": "ok", "response": {"type": "execute", "result": {}}}, {"type": "error", "error": {"message": "fail"}}, {"type": "ok", "response": {"type": "execute", "result": {}}}, {"type": "ok", "response": {"type": "execute", "result": {}}}, {"type": "close", "response": {}}]}
    with patch("mkt_flow_p0.cloud_db.requests.post", return_value=m):
        r = C2.turso_batch([{"sql": "INSERT INTO t VALUES (?)", "args": ("a",)}])
        assert "erro" in r

def test_backup_coletar(tmp_path):
    from scripts.backup_drive import coletar_arquivos
    (tmp_path / "dashboard_p1.json").write_text("{}", encoding="utf-8")
    achados = coletar_arquivos(tmp_path)
    assert any(a.endswith("dashboard_p1.json") for a in achados)

def test_atualizar_fichas_listar(tmp_path, monkeypatch, capsys):
    import scripts.atualizar_fichas as A
    fake = tmp_path / "c.json"
    fake.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(A, "CURATED", fake)
    A.listar()
    assert capsys.readouterr().out == ""  # vazio não imprime nada, mas não quebra
