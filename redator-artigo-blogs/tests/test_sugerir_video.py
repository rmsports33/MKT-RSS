"""Testes do coletor de sugestão de vídeos (puro, sem rede e sem chave)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.collectors.sugerir_video import parse_iso8601_duracao, flags_clickbait, pontuar, eh_pt


def test_parse_duracao_casos_conhecidos():
    assert parse_iso8601_duracao("PT8M32S") == 512
    assert parse_iso8601_duracao("PT1H2M3S") == 3723
    assert parse_iso8601_duracao("PT45S") == 45


def test_parse_duracao_invalido_zera():
    assert parse_iso8601_duracao("") == 0
    assert parse_iso8601_duracao("8:32") == 0
    assert parse_iso8601_duracao(None) == 0


def test_flags_clickbait_positivo_e_negativo():
    assert "clickbait" in flags_clickbait("NÃO COMPRE esse celular!!! Review")
    assert flags_clickbait("Review Galaxy S24: bateria e câmera") == []


def test_pontuar_aprovado_vence_e_curto_perde():
    base = {"titulo": "Review Fone A", "canal": "X", "canal_id": "c1", "views": 1000, "duracao_s": 500}
    aprovado = dict(base, canal_id="ok")
    curto = dict(base, duracao_s=30)
    assert pontuar(aprovado, ("ok",)) > pontuar(base, ("ok",)) > pontuar(curto, ("ok",))


def test_eh_pt_casos_conhecidos():
    assert eh_pt("Galaxy S24: análise completa, vale a pena?")
    assert eh_pt("Review Galaxy S24: câmera e bateria")
    assert not eh_pt("Samsung Galaxy S24 full review")


def test_bonus_pt_sobe_nota():
    item = {"titulo": "Análise Galaxy S24", "canal": "X", "canal_id": "c1", "views": 1000, "duracao_s": 500}
    assert pontuar(item, (), bonus_pt=2.0) == pontuar(item) + 2.0
