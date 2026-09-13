"""
Testes P0 — content_filter (offline, sem rede)
pytest tests/test_content_filter_p0.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.content_filter import filtrar_conteudo, filtrar_item_rss


def test_tecnologia_aprovada():
    r = filtrar_conteudo("Galaxy S26 Ultra: review da câmera", "Análise de bateria e zoom 5x.")
    assert r["veredito"] == "APROVADO" and r["categorias"] == []


def test_apostas_bloqueia():
    r = filtrar_conteudo("Melhor bet com bônus", "Aposta esportiva com odd de 2.0")
    assert r["veredito"] == "BLOQUEADO" and "apostas" in r["categorias"]


def test_adulto_bloqueia_sem_acento():
    assert filtrar_conteudo("Vazou privacy de famosa", "")["veredito"] == "BLOQUEADO"


def test_politica_revisa_nao_bloqueia():
    r = filtrar_conteudo("Senado vota marco da IA", "Deputados debatem texto")
    assert r["veredito"] == "REVISAR"


def test_categoria_extra():
    r = filtrar_conteudo("Sorteio de iPhone no Instagram", "", {"sorteio": [r"sorteio"]})
    assert r["veredito"] == "BLOQUEADO"


def test_gate_rss():
    r = filtrar_item_rss({"titulo": "Novo notebook", "resumo": "Review", "link": "https://x", "fonte": "blog"})
    assert r["veredito"] == "APROVADO" and r["link"] == "https://x"
