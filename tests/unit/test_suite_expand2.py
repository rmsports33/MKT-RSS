"""
Expansão 2: cobre vault/scheduler/wp/link_tracker/keyword/seo
pytest tests/unit/test_suite_expand2.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import mkt_flow_p0.vault as V
import mkt_flow_p0.scheduler as S
import mkt_flow_p0.link_tracker as L
from mkt_flow_p0.seo import template_por_categoria, canonical_url, gerar_sitemap, validar_seo_qualidade
from mkt_flow_p0.keyword_research import sugerir_keywords_review
from mkt_flow_p0.wp_publisher import publicar_no_wordpress

def test_vault_registrar_listar(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "DB_PATH", tmp_path / "v.db")
    r = V.registrar_identidade("instagram", "@canal", nicho="tech")
    assert r["identity_id"].startswith("identity_")
    assert len(V.listar_identidades("instagram")) == 1

def test_vault_compat_shopee_wordpress():
    assert V.checar_compatibilidade("shopee", "wordpress")["compativel"] is False
    assert V.checar_compatibilidade("mercado_livre", "wordpress")["compativel"] is True

def test_vault_agendar_ok_e_bloqueado(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "DB_PATH", tmp_path / "s.db")
    monkeypatch.setattr(V, "DB_PATH", tmp_path / "s.db")
    ok = V.agendar_com_programa("mercado_livre", "tiktok", "c1")
    assert ok["compativel"] is True
    bad = V.agendar_com_programa("shopee", "wordpress", "c2")
    assert bad["compativel"] is False

def test_scheduler_due_e_retry(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "DB_PATH", tmp_path / "s2.db")
    sid = S.schedule_post("c1", "instagram", "2000-01-01T00:00:00")["schedule_id"]
    assert len(S.get_due_posts("2026-01-01T00:00:00")) == 1
    assert S.mark_published(sid) is True
    assert S.get_due_posts("2026-01-01T00:00:00") == []

def test_link_tracker_registrar(tmp_path, monkeypatch):
    monkeypatch.setattr(L, "DB_PATH", tmp_path / "l.db")
    pid = L.registrar_publicacao("abc", "https://x", "wordpress", "ml", "https://w/p", "PASS")
    assert pid and len(L.listar_publicacoes("abc")) == 1
    assert L.contar_por_plataforma()["wordpress"] == 1

def test_wp_gate_publish_bloqueia():
    r = publicar_no_wordpress("T", "<p>x</p>", "FAIL", "https://w", "u", "p", status_desejado="publish")
    assert "erro" in r

def test_wp_garantir_tag_cria():
    get_vazio = MagicMock()
    get_vazio.status_code = 200
    get_vazio.json.return_value = []
    criado = MagicMock()
    criado.status_code = 201
    criado.json.return_value = {"id": 9}
    with patch("mkt_flow_p0.wp_publisher.requests.get", return_value=get_vazio), \
         patch("mkt_flow_p0.wp_publisher.requests.post", return_value=criado):
        from mkt_flow_p0.wp_publisher import garantir_tag
        assert garantir_tag("https://w", "u", "p", "Novo") == 9

def test_seo_templates():
    t = template_por_categoria("eletronicos", "Fone JBL", "299.90")
    assert len(t["title"]) <= 60 and "Fone JBL" in t["h1"]
    assert canonical_url("Fone JBL!", "https://site.com") == "https://site.com/fone-jbl"

def test_sitemap_e_qualidade():
    xml = gerar_sitemap(["https://site.com/a", "b"], base="https://site.com")
    assert "<urlset" in xml
    q = validar_seo_qualidade("<html><head><title>Um titulo com mais de dez chars</title><meta name=\"description\" content=\"d\"><link rel=\"canonical\" href=\"u\"></head><body>" + "x"*400 + "</body></html>")
    assert q["qualidade_ok"] is True

def test_keyword_fallback():
    with patch("mkt_flow_p0.keyword_research._autocomplete", return_value=[]):
        kws = sugerir_keywords_review("abc xyz", limit=2)
        assert kws[0] == "abc xyz"

def test_keyword_vazio():
    assert sugerir_keywords_review("", limit=3) == []
