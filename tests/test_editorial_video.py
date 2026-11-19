"""Testes do bloco de video: contrato de entrada, duracao e JSON-LD seguro."""
import json
import re

import pytest

from mkt_flow_p0 import editorial_video as ev

CORPO_JSONLD = re.compile(r'<script type="application/ld\+json">(.*)</script>', re.S)


def ficha(**campos):
    return {"article": dict(campos)}


def test_ficha_canonica_youtube_estrela_chega_ao_bloco():
    video = ev.extrair_video(ficha(
        youtube_id="dQw4w9WgXcQ",
        youtube_titulo="Review real do aparelho",
        youtube_canal="Canal real",
        youtube_resumo="Mostra o aparelho ligado em uso.",
        youtube_pontos=["Tela", "Bateria", "Câmera", "Construção", "Quinto item"],
        youtube_duracao="8:32",
        youtube_uploadDate="2026-10-01T12:00:00Z",
    ))
    assert video == {
        "youtube_id": "dQw4w9WgXcQ",
        "titulo": "Review real do aparelho",
        "canal": "Canal real",
        "resumo": "Mostra o aparelho ligado em uso.",
        "pontos": ["Tela", "Bateria", "Câmera", "Construção"],
        "duracao": "8:32",
        "uploadDate": "2026-10-01T12:00:00Z",
        "duracao_iso": "PT8M32S",
    }


def test_dict_curto_do_gerador_legado_e_aceito():
    video = ev.extrair_video({"video": {
        "youtube_id": "dQw4w9WgXcQ",
        "titulo": "Review real",
        "canal": "Canal real",
        "duracao": "10:00",
    }})
    assert video["titulo"] == "Review real"
    assert video["duracao"] == "10:00"
    assert video["duracao_iso"] == "PT10M"


def test_campo_desconhecido_no_video_e_rejeitado():
    with pytest.raises(ValueError, match="desconhecido"):
        ev.extrair_video({"video": {
            "youtube_id": "dQw4w9WgXcQ", "titulo": "T", "canal": "C",
            "preco": "R$ 1",
        }})


def test_campo_youtube_desconhecido_na_ficha_e_rejeitado():
    with pytest.raises(ValueError, match="youtube_ desconhecido"):
        ev.extrair_video(ficha(
            youtube_id="dQw4w9WgXcQ", youtube_titulo="T", youtube_canal="C",
            youtube_url="https://youtube.com/watch?v=dQw4w9WgXcQ",
        ))


def test_misturar_formatos_e_rejeitado():
    with pytest.raises(ValueError, match="nao misture"):
        ev.extrair_video({"video": {
            "youtube_id": "dQw4w9WgXcQ", "youtube_titulo": "T",
            "titulo": "T", "canal": "C",
        }})


def test_ficha_sem_campo_de_video_nao_cria_bloco():
    # Ausencia total de video: nada e inserido, nada e inventado.
    assert ev.extrair_video(ficha()) is None


@pytest.mark.parametrize("campos", [
    {"youtube_id": "abc", "youtube_titulo": "T", "youtube_canal": "C"},
    {"youtube_id": "dQw4w9WgXcQ", "youtube_canal": "C"},
    {"youtube_id": "dQw4w9WgXcQ", "youtube_titulo": "   ", "youtube_canal": "C"},
])
def test_ficha_com_video_invalido_reprova_o_pacote(campos):
    # Video declarado e invalido nunca vira bloco parcial: reprova o pacote.
    with pytest.raises(ValueError):
        ev.extrair_video(ficha(**campos))


def test_payload_sem_video_devolve_none():
    assert ev.extrair_video({"source_url": "https://example.org/a"}) is None


@pytest.mark.parametrize("texto,esperado", [
    ("8:32", "PT8M32S"),
    ("1:02:03", "PT1H2M3S"),
    ("0:45", "PT45S"),
    ("PT8M32S", "PT8M32S"),
    ("90:00", ""),
    ("12:99", ""),
    ("abc", ""),
    ("", ""),
])
def test_duracao_para_iso(texto, esperado):
    assert ev.duracao_para_iso(texto) == esperado


def test_duracao_textual_preserva_informacao_valida():
    video = ev.extrair_video({"video": {
        "youtube_id": "dQw4w9WgXcQ", "titulo": "T", "canal": "C",
        "duracao": "12:99",
    }})
    assert video["duracao"] == "12:99"
    assert "duracao_iso" not in video


def test_duracao_iso_invalida_e_rejeitada():
    with pytest.raises(ValueError, match="duracao_iso"):
        ev.extrair_video({"video": {
            "youtube_id": "dQw4w9WgXcQ", "titulo": "T", "canal": "C",
            "duracao_iso": "8 minutos",
        }})


def test_jsonld_neutraliza_quebra_de_script_sem_perder_texto():
    resumo = "</script><script>alert(1)</script> <!-- fim"
    saida = ev.videoobject_jsonld({
        "youtube_id": "dQw4w9WgXcQ", "titulo": "Fim",
        "canal": "C", "resumo": resumo, "duracao_iso": "PT8M32S",
    })
    achado = CORPO_JSONLD.fullmatch(saida)
    assert achado is not None
    interno = achado.group(1)
    assert "<" not in interno and ">" not in interno
    assert "</script" not in interno.lower()
    dados = json.loads(interno)
    assert dados["description"] == resumo
    assert dados["duration"] == "PT8M32S"
    assert dados["@type"] == "VideoObject"


def test_bloco_video_escapa_texto_e_mostra_duracao_e_credito():
    bloco = ev.bloco_video({
        "youtube_id": "dQw4w9WgXcQ", "titulo": "<b>T</b>",
        "canal": "C & D", "resumo": "<img src=x onerror=1>",
        "pontos": ["<i>p</i>"], "duracao": "8:32",
    })
    assert "&lt;b&gt;" in bloco and "<b>" not in bloco
    assert "&lt;img" in bloco and "<img" not in bloco
    assert "&lt;i&gt;p&lt;/i&gt;" in bloco
    assert "C &amp; D" in bloco
    assert "Duração: 8:32" in bloco
    assert "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ" in bloco
    assert "https://www.youtube.com/watch?v=dQw4w9WgXcQ" in bloco

@pytest.mark.parametrize("upload_date", [
    "2026-10-01",
    "2026-10-01T12:00:00Z",
    "2026-10-01T12:00:00-03:00",
    "2026-10-01T12:00:00.123+00:00",
])
def test_upload_date_iso8601_validas_sao_aceitas(upload_date):
    video = ev.extrair_video({"video": {
        "youtube_id": "dQw4w9WgXcQ", "titulo": "T", "canal": "C",
        "uploadDate": upload_date,
    }})
    assert video["uploadDate"] == upload_date


@pytest.mark.parametrize("upload_date", [
    "ontem",
    "2026-99-99",
    "2026-10-01T12:00:00",
    "2026-10-01T25:00:00Z",
    "2026-10-01T12:00:00+25:00",
])
def test_upload_date_invalida_reprova_o_video(upload_date):
    with pytest.raises(ValueError, match="youtube_uploadDate"):
        ev.extrair_video({"video": {
            "youtube_id": "dQw4w9WgXcQ", "titulo": "T", "canal": "C",
            "uploadDate": upload_date,
        }})

def test_upload_date_nula_permanece_opcional():
    video = ev.extrair_video({"video": {
        "youtube_id": "dQw4w9WgXcQ", "titulo": "T", "canal": "C",
        "uploadDate": None,
    }})
    assert "uploadDate" not in video
