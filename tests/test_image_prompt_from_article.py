"""Testes do prompt de imagem derivado da matéria. Sem rede, sem geração real."""
import pytest
from mkt_flow_p0.image_prompt_from_article import construir_prompt_imagem


def _artigo():
    return {
        "titulo_seo": "Anatel manda TIM desligar bloqueio de telemarketing",
        "meta_description": "Decisão cautelar dá 24 horas para desligar ferramenta antispam.",
        "conteudo_markdown": (
            "<p>A Anatel determinou que a TIM desligue a ferramenta antispam "
            "de telemarketing abusivo em 24 horas, por falta de transparência.</p>"
        ),
        "fontes": ["https://tecnoblog.net/noticias/exemplo", {"url": "https://anatel.gov.br/noticia"}],
    }


def test_prompt_usa_titulo_da_materia():
    out = construir_prompt_imagem(_artigo())
    assert "Anatel manda TIM desligar bloqueio de telemarketing" in out["prompt"]


def test_prompt_usa_subtitulo():
    out = construir_prompt_imagem(_artigo())
    assert "24 horas" in out["prompt"]


def test_prompt_detecta_tema_pelo_conteudo():
    out = construir_prompt_imagem(_artigo())
    assert any("telemarketing" in t.lower() for t in out["base_do_artigo"]["temas_detectados"])


def test_prompt_proibe_logos_e_fatos_inventados():
    out = construir_prompt_imagem(_artigo())
    assert "NÃO inclua logos" in out["prompt"]
    assert "sem_fatos_inventados" in out["constraints"]


def test_fontes_https_extraidas():
    out = construir_prompt_imagem(_artigo())
    assert "https://tecnoblog.net/noticias/exemplo" in out["fontes"]
    assert "https://anatel.gov.br/noticia" in out["fontes"]


def test_sem_titulo_bloqueia():
    with pytest.raises(ValueError, match="ARTIGO_SEM_TITULO"):
        construir_prompt_imagem({"conteudo_markdown": "<p>Texto</p>"})


def test_artigo_invalido_bloqueia():
    with pytest.raises(ValueError, match="ARTIGO_INVALIDO"):
        construir_prompt_imagem("nao e dict")
