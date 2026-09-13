"""
Expansão 5: cobertura final para 244 — edge, seo, vault, alerts, pipeline
pytest tests/unit/test_suite_expand5.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from mkt_flow_p0.seo import gerar_faq_schema, gerar_faq_review, gerar_llms_txt, validar_seo_qualidade
from mkt_flow_p0.vault import get_platform_limits
from mkt_flow_p0.validator import validar_link_afiliado
from mkt_flow_p0.roi import calcular_roi_afiliado

def test_faq_schema_vazio():
    assert gerar_faq_schema([]) == ""
    assert "FAQPage" in gerar_faq_schema([{"pergunta": "P?", "resposta": "R."}])

def test_faq_review():
    faqs = gerar_faq_review("Fone X", "199.90", "Shopee")
    assert len(faqs) == 3 and "Fone X" in faqs[0]["pergunta"]

def test_llms_txt():
    txt = gerar_llms_txt("https://site.com", ["https://site.com/a", "b"])
    assert "site.com/a" in txt and "site.com/b" in txt

def test_seo_qualidade_falha():
    q = validar_seo_qualidade("<html></html>")
    assert q["qualidade_ok"] is False

def test_vault_limites():
    assert get_platform_limits("instagram")["max_posts_per_day"] == 5
    assert get_platform_limits("desconhecida")["max_posts_per_day"] == 5

def test_validator_vazio():
    assert validar_link_afiliado("", resolver_redirect=False)["status_validacao"] == "FAIL"

def test_validator_meli_sem_tag():
    assert validar_link_afiliado("https://www.mercadolivre.com.br/x", resolver_redirect=False)["status_validacao"] == "FAIL"

def test_validator_shopee():
    r = validar_link_afiliado("https://shopee.com.br/x", resolver_redirect=False)
    assert r["status_validacao"] == "UNKNOWN"

def test_roi_com_deducao():
    r = calcular_roi_afiliado(1, 100, 10.0, 100.0, 10.0, deducao_pct=10)
    assert r["comissao_liquida_brl"] == 90.0

def test_roi_zero():
    r = calcular_roi_afiliado(0, 0, 0, 0, 0)
    assert r["custo_ads_brl"] == 0

def test_extractor_url_invalida():
    from mkt_flow_p0.extractor import extrair_conteudo
    assert "erro" in extrair_conteudo("nota-url")

def test_rss_ingestor_sem_feedparser(monkeypatch):
    import mkt_flow_p0.rss_ingestor as R
    monkeypatch.setattr(R, "_HAS_FEEDPARSER", False)
    assert "erro" in R.fetch_feed("https://x")

def test_cloud_desligado(monkeypatch):
    import mkt_flow_p0.cloud_db as C
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    assert C.turso_enabled() is False

def test_backup_empacotar(tmp_path):
    from scripts.backup_drive import empacotar
    import zipfile
    f = tmp_path / "a.txt"
    f.write_text("oi", encoding="utf-8")
    z = empacotar([str(f)], tmp_path)
    assert zipfile.is_zipfile(z)

def test_atualizar_fichas_criar(tmp_path, monkeypatch):
    import scripts.atualizar_fichas as A
    fake = tmp_path / "c.json"
    fake.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(A, "CURATED", fake)
    A.salvar_ficha("Teste", "geral", {"a": "1"}, "f")
    assert len(A._carregar()) == 1

def test_format_bold():
    from mkt_flow_p0.format import markdown_para_html
    assert "<strong>" in markdown_para_html("**oi**")

def test_content_filter_bloqueio():
    from mkt_flow_p0.content_filter import filtrar_conteudo
    assert filtrar_conteudo("aposta bet365", "")["veredito"] == "BLOQUEADO"

def test_content_filter_tema():
    from mkt_flow_p0.content_filter import filtrar_por_tema
    assert filtrar_por_tema("Galaxy S24 review", "")["veredito"] == "APROVADO"
    assert filtrar_por_tema("Fase da lua", "")["veredito"] == "BLOQUEADO"

def test_scheduler_limits():
    from mkt_flow_p0.scheduler import get_platform_limits
    assert get_platform_limits("tiktok")["max_posts_per_day"] == 10

def test_link_tracker_contar(tmp_path, monkeypatch):
    import mkt_flow_p0.link_tracker as L
    monkeypatch.setattr(L, "DB_PATH", tmp_path / "l.db")
    L.registrar_publicacao("id1", "https://x", "wordpress", "ml", "https://w", "PASS")
    assert L.contar_por_plataforma()["wordpress"] == 1
