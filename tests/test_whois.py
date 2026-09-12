"""
Testes básicos do whois_tool - verifica itens 1-6.
pytest tests/test_whois.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from whois_tool.parser import parse_whois
from whois_tool.robust import sanitize_and_normalize, validate_domain, detect_query_type
from whois_tool.cache import WhoisCache


def test_parse_basico():
    raw = "Domain Name: EXEMPLO.COM\nRegistrar: X\nCreation Date: 2020-01-01\nDomain Status: active\nName Server: A.EX.COM\n"
    p = parse_whois(raw)
    assert p["domain"] == "exemplo.com" and p["nameservers"] == ["a.ex.com"]


def test_sanitize():
    assert sanitize_and_normalize("https://Exemplo.com/caminho") == "exemplo.com"


def test_validate():
    assert validate_domain("exemplo.com")["valido"] is True
    assert validate_domain("..ruim")["valido"] is False


def test_tipo_consulta():
    assert detect_query_type("8.8.8.8") == "ip"
    assert detect_query_type("exemplo.com") == "domain"


def test_cache(tmp_path):
    c = WhoisCache(db_path=tmp_path / "w.db", ttl=60)
    assert c.get("exemplo.com") is None
    c.set("exemplo.com", "RAW")
    assert c.get("exemplo.com") == "RAW"
