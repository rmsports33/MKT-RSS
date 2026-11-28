"""Padrão vivo: artigos aprovados viram referência de estrutura, não de texto."""
import json

import pytest

from mkt_flow_p0 import editorial_golden_set as gs
from mkt_flow_p0.rewriter import montar_prompt

BRIEF = {
    "genre": "analise",
    "reader": "Leitor brasileiro de tecnologia que quer entender o tema.",
    "need": "Entender quando a eficiência muda o consumo total.",
    "angle": "Explicar o paradoxo com limites explícitos.",
    "contribution": "Critérios para ler manchetes com segurança.",
    "limits": "Não inventar preços nem contexto brasileiro.",
}
TEXTO = ("A pergunta é se eficiência reduz gasto. A tese é que depende da elasticidade. "
         "Segundo a literatura, o efeito rebound pode anular a economia. "
         "Na prática, isso afeta decisões. Mas os estudos divergem sobre a magnitude. "
         "Em síntese, o veredito é condicional aos fatos.")


@pytest.fixture
def caminho(tmp_path, monkeypatch):
    destino = tmp_path / "golden.json"
    monkeypatch.setenv("CONEXO_GOLDEN_SET_PATH", str(destino))
    return destino


def test_registrar_exige_aprovacao_e_nota_humana(caminho):
    with pytest.raises(ValueError):
        gs.registrar(TEXTO, genero="analise", nota_humana=88, nota_assistida=90,
                     artigo_id="1")
    with pytest.raises(ValueError):
        gs.registrar(TEXTO, genero="analise", nota_humana=50, nota_assistida=90,
                     artigo_id="1", aprovado_por_humano=True, fato_conferido=True)


def test_registrar_e_deduplicar(caminho):
    kwargs = dict(genero="analise", nota_humana=88, nota_assistida=90,
                  artigo_id="9925", aprovado_por_humano=True, fato_conferido=True)
    gs.registrar(TEXTO, **kwargs)
    gs.registrar(TEXTO, **kwargs)
    assert len(gs.carregar()["generos"]["analise"]) == 1
    assert gs.resumo()["por_genero"]["analise"] == 1


def test_bloco_prompt_nao_copia_texto(caminho):
    frase = "A tese é que depende da elasticidade."
    gs.registrar(TEXTO, genero="analise", nota_humana=88, nota_assistida=90,
                 artigo_id="9925", aprovado_por_humano=True, fato_conferido=True)
    bloco = gs.bloco_prompt("analise")
    assert "nota humana 88/100" in bloco
    assert frase not in bloco


def test_montar_prompt_inclui_padrao_quando_há_aprovacao(caminho):
    antes = montar_prompt("Título", " ".join(["insumo"] * 110), "Fonte",
                          editorial_brief=BRIEF)
    gs.registrar(TEXTO, genero="analise", nota_humana=91, nota_assistida=90,
                 artigo_id="9926", aprovado_por_humano=True, fato_conferido=True)
    depois = montar_prompt("Título", " ".join(["insumo"] * 110), "Fonte",
                           editorial_brief=BRIEF)
    assert "PADRÃO EDITORIAL DE ALTA NOTA" not in antes
    assert "PADRÃO EDITORIAL DE ALTA NOTA" in depois


def test_sem_padrao_nao_muda_nada(caminho):
    assert gs.selecionar("analise") is None
    assert gs.bloco_prompt("analise") == ""
