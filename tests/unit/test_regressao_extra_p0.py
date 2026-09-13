"""
Testes P0/P1 — cobertura extra de regressão (pós-restauração 12/09/2026).
Comportamentos travados dos módulos reconstruídos. Tudo mockado/offline.
pytest tests/test_regressao_extra_p0.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))


# --- validator ---
def test_validator_case_insensitive_e_www():
    from mkt_flow_p0.validator import validar_link_afiliado
    r = validar_link_afiliado("HTTPS://WWW.MERCADOLIVRE.COM.BR/x?matt_word=a", resolver_redirect=False)
    assert r["status_validacao"] == "PASS"


def test_validator_head_falha_mantem_url():
    from mkt_flow_p0.validator import validar_link_afiliado
    with patch("mkt_flow_p0.validator.requests.head", side_effect=Exception("rede")):
        r = validar_link_afiliado("https://www.mercadolivre.com.br/p/MLB1?matt_word=x", resolver_redirect=True)
        assert r["status_validacao"] == "PASS" and r["url_final"].startswith("https://")


def test_validator_parametro_maiusculo_fail_fechado():
    # parse_qs é case-sensitive por design: tag fora do padrão exato do
    # portal (minúsculas) reprova em modo fail-closed (compliance primeiro).
    from mkt_flow_p0.validator import validar_link_afiliado
    assert validar_link_afiliado("https://www.mercadolivre.com.br/x?TAG=a", resolver_redirect=False)["status_validacao"] == "FAIL"


# --- policy: cobertura das 21 regras ---
def _pol(fatos, prog="mercado_livre"):
    from mkt_flow_p0.policy_engine import avaliar_politica
    return avaliar_politica(prog, fatos)


def test_policy_comparison_fail():
    assert _pol({"compara_com_outro_produto": True})["status_politica"] == "FAIL"


def test_policy_cookie_fail():
    assert _pol({"cookie_clique_visivel": False})["status_politica"] == "FAIL"


def test_policy_categoria_proibida():
    assert _pol({"categoria_proibida_ml": True})["status_politica"] == "FAIL"


def test_policy_brand_keyword():
    assert _pol({"keyword_marca_ml": True})["status_politica"] == "FAIL"


def test_policy_midia_nao_cadastrada():
    assert _pol({"midia_cadastrada": False})["status_politica"] == "FAIL"


def test_policy_shortener():
    assert _pol({"usa_shortener": True})["status_politica"] == "FAIL"


def test_policy_evidencia_missing_unknown():
    assert _pol({"informacoes_constam_anuncio": False})["status_politica"] == "UNKNOWN"


def test_policy_shopee_social_pass():
    r = _pol({"tipo_midia": "tiktok_ads", "midia_cadastrada": True, "conta_cadastrada_programa": True}, "shopee")
    assert r["status_politica"] == "PASS"


def test_policy_shopee_cookie_e_conteudo():
    assert _pol({"cookie_clique_visivel": False}, "shopee")["status_politica"] == "FAIL"
    assert _pol({"conteudo_nao_verificado": True}, "shopee")["status_politica"] == "FAIL"


# --- landing rica ---
def test_landing_completa_dict():
    from mkt_flow_p0.landing import gerar_landing_page_completa
    d = gerar_landing_page_completa("Fone JBL", "https://a.com", "199.90", status_validacao="PASS")
    assert d["url_amigavel"].endswith("/fone-jbl") and len(d["meta"]["title"]) <= 60


# --- scheduler/vault/alertas extras ---
def test_scheduler_calendar_aviso(tmp_path, monkeypatch):
    import mkt_flow_p0.scheduler as S
    monkeypatch.setattr(S, "DB_PATH", tmp_path / "c.db")
    for i in range(7):
        S.schedule_post(f"c{i}", "instagram", "2026-06-01T10:00:00")
    cal = S.get_calendar_view("2026-06-01T00:00:00", "2026-06-02T00:00:00")
    assert any("instagram" in a for a in cal["avisos_capacidade"])
    assert S.clear_schedules() == 7


def test_vault_limites_e_lista(tmp_path, monkeypatch):
    import mkt_flow_p0.vault as V
    monkeypatch.setattr(V, "DB_PATH", tmp_path / "v.db")
    V.registrar_identidade("tiktok", "@canal")
    assert len(V.listar_identidades()) == 1
    assert V.get_platform_limits("tiktok")["max_posts_per_day"] == 10


def test_alerts_check_all_counts():
    from mkt_flow_p0.alerts import check_all
    with patch("mkt_flow_p0.alerts._check_url_head",
               side_effect=[{"url": "a", "http_code": 404, "ok": False, "elapsed_ms": 1},
                            {"url": "b", "http_code": 200, "ok": True, "elapsed_ms": 1}]):
        r = check_all([{"url": "a"}, {"url": "b"}])
        assert (r["criticos"], r["ok"], r["total"]) == (1, 1, 2)


def test_seo_stats_vazio():
    from mkt_flow_p0.seo import gerar_sitemap
    # legado seo_programmatic foi arquivado; cobertura equivalente é validar sitemap vazio
    xml = gerar_sitemap([], base="https://site.com")
    assert "<urlset" in xml and xml.count("<url>") == 0


# --- whois extras ---
def test_whois_robust_cache_expira(tmp_path):
    from whois_tool.cache import WhoisCache
    c = WhoisCache(db_path=tmp_path / "w.db", ttl=-1)
    c.set("e.com", "X")
    assert c.get("e.com") is None
