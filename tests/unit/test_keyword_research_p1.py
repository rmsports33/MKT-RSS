"""
Testes P1 — keyword research (autocomplete mockado)
pytest tests/test_keyword_research_p1.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.keyword_research import sugerir_keywords_review


def test_sugere_com_autocomplete():
    with patch("mkt_flow_p0.keyword_research._autocomplete", return_value=["fone jbl preço", "fone jbl vale a pena"]):
        kws = sugerir_keywords_review("fone jbl", limit=4)
        assert "fone jbl preço" in kws and len(kws) <= 4


def test_fallback_sem_internet():
    with patch("mkt_flow_p0.keyword_research._autocomplete", return_value=[]):
        kws = sugerir_keywords_review("fone jbl", limit=3)
        assert kws and kws[0] == "fone jbl"


def test_nome_vazio():
    assert sugerir_keywords_review("", limit=5) == []
