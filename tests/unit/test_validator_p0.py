"""
Testes P0 — validator PASS/FAIL/UNKNOWN (mock de rede)
pytest tests/test_validator_p0.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.validator import validar_link_afiliado, resolve, validar_lote, resumo_validacao


def test_ml_com_tag_pass():
    r = validar_link_afiliado("https://www.mercadolivre.com.br/oferta?matt_word=abc", resolver_redirect=False)
    assert r["status_validacao"] == "PASS"
    assert r["valido"] is True
    assert r["plataforma"] == "Mercado Livre"
    assert r["possui_tag_rastreio"] is True


def test_ml_sem_tag_fail():
    r = validar_link_afiliado("https://www.mercadolivre.com.br/oferta", resolver_redirect=False)
    assert r["status_validacao"] == "FAIL"
    assert r["valido"] is False
    assert r["possui_tag_rastreio"] is False


def test_ml_sec_shortlink_pass():
    r = validar_link_afiliado("https://mercadolivre.com/sec/MLB123?matt_tool=x", resolver_redirect=False)
    assert r["status_validacao"] == "PASS"


def test_shopee_unknown_nunca_pass():
    r = validar_link_afiliado("https://shopee.com.br/produto?x=1", resolver_redirect=False)
    assert r["status_validacao"] == "UNKNOWN"
    assert r["valido"] is None
    assert r["possui_tag_rastreio"] is None


def test_dominio_fora_fail():
    r = validar_link_afiliado("https://loja-qualquer.com/produto", resolver_redirect=False)
    assert r["status_validacao"] == "FAIL"


def test_url_vazia_fail():
    assert validar_link_afiliado("", resolver_redirect=False)["status_validacao"] == "FAIL"


def test_resolve_alias_e_redirect_mock():
    class Resp:
        url = "https://www.mercadolivre.com.br/p/MLB123?matt_word=x"
    with patch("mkt_flow_p0.validator.requests.head", return_value=Resp()):
        r = validar_link_afiliado("https://mercadolivre.com/sec/abc?matt_word=x", resolve=True)
        assert r["url_final"] == Resp.url
        assert resolve("https://mercadolivre.com/sec/abc?matt_word=x") == Resp.url


def test_destino_produto_vs_generico():
    r = validar_link_afiliado("https://www.mercadolivre.com.br/p/MLB123?matt_word=x", resolver_redirect=False)
    assert r["destino"] == "produto"
    r2 = validar_link_afiliado("https://www.mercadolivre.com.br/ofertas?matt_word=x", resolver_redirect=False)
    assert r2["destino"] == "generico"
    assert "aviso" in r2


def test_lote_e_resumo():
    rs = validar_lote(["https://shopee.com.br/a", "https://x.com"], resolver_redirect=False)
    s = resumo_validacao(rs)
    assert s["total"] == 2 and s["UNKNOWN"] == 1 and s["FAIL"] == 1


def test_ml_wid_fragmento_pass():
    # Formato novo do Link Especial: tag wid/sid no fragmento (#)
    r = validar_link_afiliado(
        "https://www.mercadolivre.com.br/monitor-gamer-27/p/MLB64311324#polycard_client=affiliates&wid=MLB6194005242&sid=affiliates",
        resolver_redirect=False,
    )
    assert r["status_validacao"] == "PASS"
    assert r["possui_tag_rastreio"] is True
    assert r["destino"] == "produto"


def test_ml_sid_query_pass():
    r = validar_link_afiliado(
        "https://www.mercadolivre.com.br/monitor-gamer-27/p/MLB64311324?sid=affiliates&wid=MLB6194005242",
        resolver_redirect=False,
    )
    assert r["status_validacao"] == "PASS"


def test_ml_social_com_wid_bloqueia():
    # Mesmo com wid, link de perfil social não é anúncio de produto
    r = validar_link_afiliado(
        "https://www.mercadolivre.com.br/social/reinaldomcarvalho?matt_word=conexotech&matt_tool=39107843",
        resolver_redirect=False,
    )
    assert r["status_validacao"] in ("FAIL", "UNKNOWN")
