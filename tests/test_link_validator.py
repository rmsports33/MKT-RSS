"""
Testes legados — MKTFLOW.link_validator
pytest tests/test_link_validator.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "MKTFLOW"))
sys.path.insert(0, str(Path(__file__).parent.parent))
from MKTFLOW.link_validator import validar_link_afiliado, PADRAO_MELI, PADRAO_SHOPEE


def test_padroes():
    assert PADRAO_MELI.match("https://www.mercadolivre.com.br/x?matt_word=a")
    assert PADRAO_MELI.match("https://mercadolivre.com/sec/abc?matt_word=a")
    assert PADRAO_SHOPEE.match("https://s.shopee.com.br/x")
    assert not PADRAO_MELI.match("https://x.com")


def test_ml_ok_e_sem_tag():
    assert validar_link_afiliado("https://www.mercadolivre.com.br/x?tag=a")["valido"] is True
    assert validar_link_afiliado("https://www.mercadolivre.com.br/x")["valido"] is False


def test_shopee_unknown():
    r = validar_link_afiliado("https://shopee.com.br/x")
    assert r["status_validacao"] == "UNKNOWN" and r["valido"] is None
