"""Validacao estrita dos formatos de video, uniforme em todas as localizacoes.

Cada caso invalido reprova o pacote inteiro: nada vira video parcial, nada e
ignorado em silencio e nada e completado por inferencia.
"""
from unittest.mock import patch

import pytest

from mkt_flow_p0 import editorial_video as ev
from mkt_flow_p0.editorial_import import _preparar_handoff, processar_artigo_importado

CANONICO = {
    "youtube_id": "dQw4w9WgXcQ",
    "youtube_titulo": "Review real do aparelho",
    "youtube_canal": "Canal real",
}
CURTO = {
    "youtube_id": "dQw4w9WgXcQ",
    "titulo": "Review real do aparelho",
    "canal": "Canal real",
}
ESPERADO = {
    "youtube_id": "dQw4w9WgXcQ",
    "titulo": "Review real do aparelho",
    "canal": "Canal real",
}


def artigo(**extra):
    base = {"titulo_seo": "Titulo do artigo", "slug": "titulo-do-artigo"}
    base.update(extra)
    return base


# --- formatos validos preservados -------------------------------------------


def test_canonico_valido_na_raiz():
    assert ev.extrair_video(dict(CANONICO)) == ESPERADO


def test_canonico_valido_em_article():
    assert ev.extrair_video({"article": artigo(**CANONICO)}) == ESPERADO


def test_canonico_valido_em_metadata():
    assert ev.extrair_video({"metadata": artigo(**CANONICO)}) == ESPERADO


def test_canonico_valido_dentro_de_video():
    assert ev.extrair_video({"video": dict(CANONICO)}) == ESPERADO


def test_curto_valido_dentro_de_video():
    assert ev.extrair_video({"video": dict(CURTO)}) == ESPERADO


def test_curto_valido_na_raiz():
    assert ev.extrair_video(dict(CURTO)) == ESPERADO


def test_campos_opcionais_do_canonico_preservados():
    video = ev.extrair_video({"video": dict(
        CANONICO,
        youtube_resumo="Mostra o aparelho em uso.",
        youtube_pontos=["Tela", "Bateria"],
        youtube_duracao="8:32",
        youtube_uploadDate="2026-10-01T12:00:00Z",
    )})
    assert video["resumo"] == "Mostra o aparelho em uso."
    assert video["pontos"] == ["Tela", "Bateria"]
    assert video["duracao"] == "8:32"
    assert video["duracao_iso"] == "PT8M32S"
    assert video["uploadDate"] == "2026-10-01T12:00:00Z"


# --- campo youtube_* desconhecido em cada localizacao -----------------------


@pytest.mark.parametrize("chave,payload", [
    ("video", {"video": dict(CANONICO, youtube_url="https://youtu.be/dQw4w9WgXcQ")}),
    ("article", {"article": artigo(**dict(CANONICO, youtube_url="https://youtu.be/x"))}),
    ("metadata", {"metadata": artigo(**dict(CANONICO, youtube_capa="capa.jpg"))}),
    ("root", dict(CANONICO, youtube_url="https://youtu.be/dQw4w9WgXcQ")),
])
def test_youtube_desconhecido_e_recusado_em_todas_as_localizacoes(chave, payload):
    with pytest.raises(ValueError, match="youtube_ desconhecido em " + chave):
        ev.extrair_video(payload)


def test_youtube_desconhecido_sem_campo_valido_tambem_e_recusado():
    # Antes da correcao, um `youtube_*` estranho sozinho passava em silencio.
    with pytest.raises(ValueError, match="youtube_ desconhecido em article"):
        ev.extrair_video({"article": artigo(youtube_extra="x")})


# --- campo desconhecido em bloco canonico -----------------------------------


@pytest.mark.parametrize("local", ["video"])
def test_campo_desconhecido_em_bloco_canonico_e_recusado(local):
    bloco = dict(CANONICO, preco="R$ 1.999")
    payload = {"video": bloco} if local == "video" else bloco
    with pytest.raises(ValueError, match="campo de video desconhecido em " + local):
        ev.extrair_video(payload)


def test_campo_desconhecido_na_raiz_nao_e_confundido_com_video():
    # Na raiz o dicionario e o proprio pacote: so campos de video contam.
    video = ev.extrair_video({"source_url": "https://example.org/a",
                              "source_name": "Fonte", **CANONICO})
    assert video == ESPERADO


def test_campo_de_artigo_nao_e_confundido_com_video():
    # Em ficha real, campos do artigo convivem com o video e nao sao recusados.
    assert ev.extrair_video({"article": artigo(**CANONICO)}) == ESPERADO


# --- mistura de formatos ----------------------------------------------------


@pytest.mark.parametrize("payload", [
    {"video": dict(CANONICO, titulo="Outro titulo")},
    {"video": dict(CANONICO, canal="Outro canal")},
    {"article": artigo(**dict(CANONICO, canal="Outro canal"))},
    {"metadata": artigo(**dict(CANONICO, duracao="8:32"))},
    dict(CANONICO, resumo="Resumo curto"),
])
def test_mistura_de_canonico_com_curto_e_recusada(payload):
    with pytest.raises(ValueError, match="nao misture"):
        ev.extrair_video(payload)


# --- formatos incompletos ---------------------------------------------------


@pytest.mark.parametrize("payload", [
    {"article": artigo(youtube_id="dQw4w9WgXcQ", youtube_titulo="Titulo")},
    {"article": artigo(youtube_id="dQw4w9WgXcQ", youtube_canal="Canal")},
    {"article": artigo(youtube_titulo="Titulo", youtube_canal="Canal")},
    {"video": {"youtube_id": "dQw4w9WgXcQ", "youtube_titulo": "Titulo"}},
    {"video": {"youtube_id": "dQw4w9WgXcQ", "titulo": "Titulo"}},
    {"video": {"youtube_id": "dQw4w9WgXcQ"}},
    {"video": {"titulo": "Titulo", "canal": "Canal"}},
])
def test_formato_incompleto_reprova_o_pacote(payload):
    with pytest.raises(ValueError, match="video incompleto ou invalido"):
        ev.extrair_video(payload)


def test_ficha_canonica_vazia_nao_declara_video():
    assert ev.extrair_video({"article": artigo()}) is None


def test_video_vazio_e_ambiguo_e_recusado():
    with pytest.raises(ValueError, match="video vazio"):
        ev.extrair_video({"video": {}})


# --- tipos incorretos -------------------------------------------------------


@pytest.mark.parametrize("payload,erro", [
    ("texto", "payload de video deve ser dicionario"),
    ({"video": "dQw4w9WgXcQ"}, "video deve ser dicionario"),
    ({"article": ["x"]}, "article deve ser dicionario"),
    ({"metadata": 7}, "metadata deve ser dicionario"),
    ({"video": dict(CANONICO, youtube_id=123)}, "video incompleto ou invalido"),
    ({"video": dict(CURTO, youtube_id=None)}, "video incompleto ou invalido"),
    ({"video": dict(CANONICO, youtube_pontos="Tela")}, "youtube_pontos deve ser lista"),
    ({"video": dict(CANONICO, youtube_pontos=[{"a": 1}])}, "youtube_pontos invalido"),
    ({"video": dict(CANONICO, youtube_pontos=["Tela", None])}, "youtube_pontos invalido"),
    ({"video": dict(CANONICO, youtube_pontos=[""])}, "youtube_pontos com item vazio"),
    ({"video": dict(CANONICO, youtube_resumo=42)}, "campo de video invalido"),
    ({"video": dict(CANONICO, youtube_duracao=["8:32"])}, "campo de video invalido"),
    ({"video": dict(CANONICO, youtube_uploadDate=20261001)}, "campo de video invalido"),
    ({"video": dict(CANONICO, youtube_duracao_iso="8 minutos")}, "youtube_duracao_iso invalida"),
])
def test_tipos_incorretos_reprovam_o_pacote(payload, erro):
    with pytest.raises(ValueError, match=erro):
        ev.extrair_video(payload)


def test_id_do_youtube_invalido_reprova_o_pacote():
    for ruim in ("abc", "dQw4w9WgXcQx", "dQw4w9 gXcQ"):
        with pytest.raises(ValueError, match="youtube_id invalido"):
            ev.extrair_video({"video": dict(CANONICO, youtube_id=ruim)})


# --- mais de uma origem -----------------------------------------------------


@pytest.mark.parametrize("payload,origens", [
    ({"video": dict(CANONICO), "article": artigo(**dict(CANONICO, youtube_canal="Outro"))},
     "video, article"),
    ({"article": artigo(**CANONICO), **CURTO}, "article, root"),
    ({"metadata": artigo(**CANONICO), "video": dict(CANONICO)}, "video, metadata"),
    ({"video": dict(CANONICO), "metadata": artigo(**CANONICO), **CANONICO},
     "video, metadata, root"),
])
def test_mais_de_uma_origem_de_video_e_conflito(payload, origens):
    with pytest.raises(ValueError, match="mais de uma origem: " + origens):
        ev.extrair_video(payload)


# --- ausencia de video ------------------------------------------------------


@pytest.mark.parametrize("payload", [
    {},
    {"source_url": "https://example.org/a", "source_name": "Fonte"},
    {"article": artigo()},
    {"article": {"titulo_seo": "T", "canal_do_artigo": "editorial"}},
    {"metadata": artigo(), "research": {"sources": []}},
])
def test_sem_video_nao_cria_bloco(payload):
    assert ev.extrair_video(payload) is None


# --- validacao antes da normalizacao ---------------------------------------


def test_validacao_acontece_antes_da_normalizacao():
    with patch.object(ev, "_normalizar",
                      side_effect=AssertionError("normalizou entrada invalida")):
        with pytest.raises(ValueError, match="campo de video desconhecido"):
            ev.extrair_video({"video": dict(CANONICO, preco="R$ 1")})


# --- pacote inteiro rejeitado, sem renderizacao parcial ---------------------


def payload_valido():
    return {
        "source_url": "https://example.org/source",
        "source_name": "Primary source",
        "article": {
            "titulo_seo": "Guia editorial documentado",
            "meta_description": ("Guia documentado e atribuido com explicacoes praticas "
                                 "e limites claros, pendente de revisao humana."),
            "slug": "guia-editorial-documentado",
            "texto_markdown": ("## Primeira secao\n\n" + (
                "Explicacao clara e atribuida para leitores, sem experiencia "
                "inventada ou promessa de resultado. " * 22)),
        },
        "research": {"sources": [{
            "name": "Fonte adicional",
            "url": "https://example.com/additional",
            "facts": ["Uma fonte documenta o recurso explicado."],
        }]},
    }


@pytest.mark.parametrize("video_invalido", [
    {"video": dict(CANONICO, youtube_url="https://youtu.be/x")},
    {"video": dict(CANONICO, preco="R$ 1")},
    {"video": dict(CANONICO, titulo="Outro")},
    {"video": {"youtube_id": "dQw4w9WgXcQ"}},
    {"video": "abc"},
])
def test_importacao_rejeita_o_pacote_inteiro_sem_criar_saida(tmp_path, video_invalido):
    dados = payload_valido()
    dados.update(video_invalido)
    destino = tmp_path / "saida"
    with pytest.raises(ValueError):
        _preparar_handoff(dados)
    with pytest.raises(ValueError):
        processar_artigo_importado(dados, destino)
    assert not destino.exists()


@pytest.mark.parametrize("video_valido", [
    {"video": dict(CANONICO)},
    {"article_extra": dict(CANONICO)},
    dict(CANONICO),
])
def test_pacote_valido_continua_chegando_ao_handoff(tmp_path, video_valido):
    dados = payload_valido()
    if "article_extra" in video_valido:
        dados["article"].update(video_valido["article_extra"])
    else:
        dados.update(video_valido)
    handoff = _preparar_handoff(dados)
    assert handoff["metadata"]["title"] == "Guia editorial documentado"
