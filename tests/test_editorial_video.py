"""Curadoria de vídeo: só dados reais entram no bloco do artigo."""
from mkt_flow_p0.editorial_video import bloco_video, extrair_video, videoobject_jsonld

VALIDO = {
    "youtube_id": "dQw4w9WgXcQ",
    "youtube_titulo": "Análise real do aparelho",
    "youtube_canal": "Canal de reviews técnicos",
    "youtube_resumo": "Mostra a tela ligada e a câmera em uso.",
    "youtube_pontos": ["Tela em uso", "Bateria em teste"],
    "youtube_duracao_iso": "PT8M32S",
    "youtube_uploadDate": "2026-11-01",
}


def test_sem_dados_nao_gera_bloco():
    assert extrair_video({}) is None
    assert extrair_video({"video": {"youtube_id": "curto"}}) is None


def test_id_invalido_bloqueia():
    dados = dict(VALIDO, youtube_id="curto")
    assert extrair_video({"video": dados}) is None


def test_bloco_tem_player_nocookie_credito_e_link():
    video = extrair_video({"video": VALIDO})
    bloco = bloco_video(video)
    assert "youtube-nocookie.com/embed/dQw4w9WgXcQ" in bloco
    assert "Canal de reviews técnicos" in bloco
    assert "Assistir no YouTube" in bloco
    assert "O que dizem os reviews em vídeo" in bloco


def test_jsonld_e_videoobject_sem_anos_inventados():
    video = extrair_video({"video": VALIDO})
    ld = videoobject_jsonld(video)
    assert '"@type": "VideoObject"' in ld
    assert "dQw4w9WgXcQ" in ld
    assert '"uploadDate": "2026-11-01"' in ld


def test_pontos_limitados_a_quatro():
    dados = dict(VALIDO, youtube_pontos=["a", "b", "c", "d", "e"])
    video = extrair_video({"video": dados})
    assert len(video["pontos"]) == 4
