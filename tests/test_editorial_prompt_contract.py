"""Contract tests across news, guides, analysis and comparisons."""
import pytest
from mkt_flow_p0.editorial_prompt_contract import prepare_editorial_request


@pytest.mark.parametrize("genre", ["noticia", "guia", "analise", "comparativo", "review", "nota_breve"])
def test_all_genres_use_same_pre_generation_contract(genre):
    brief = {
        "genre": genre,
        "reader": "Leitores que precisam compreender a mudança e decidir o que fazer.",
        "need": "Explicar consequências práticas sem repetir a documentação original.",
        "angle": "Comparar evidências e incertezas relevantes ao público brasileiro.",
        "contribution": "Oferecer critérios de decisão verificáveis e contextualizados.",
        "limits": "Não inventar dados, entrevistas, experiências ou informações ausentes.",
    }
    payload = {"verified_sources": ["fonte original"]}
    request = prepare_editorial_request("Respeite as fontes.", payload, brief, genre=genre)
    assert "BRIEFING EDITORIAL" in request["system"]
    assert "Voz independente" in request["system"]
    assert request["payload"] is payload
    assert request["genre"] == genre


def test_genre_mismatch_blocks_before_model_call():
    brief = {
        "genre": "guia",
        "reader": "Leitores que precisam compreender a mudança e decidir o que fazer.",
        "need": "Explicar consequências práticas sem repetir a documentação original.",
        "angle": "Comparar evidências e incertezas relevantes ao público brasileiro.",
        "contribution": "Oferecer critérios de decisão verificáveis e contextualizados.",
        "limits": "Não inventar dados, entrevistas, experiências ou informações ausentes.",
    }
    with pytest.raises(ValueError, match="gênero"):
        prepare_editorial_request("Base", {}, brief, genre="noticia")
