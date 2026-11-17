"""MKT-RSS #114: fila de correcao derivada de metadados de listagem.

Nenhum teste aprova ou publica. Apenas classifica e agrega diagnosticos.
"""
from mkt_flow_p0.editorial_correction_queue import (
    classificar_rascunho, build_correction_queue)

BASE = {
    "id": 9813, "status": "draft", "slug": "noticia-verificada",
    "categories": [10], "featured_media": 456,
    "title": "Noticia verificada sobre tecnologia",
    "link": "https://conexotech.com.br/?p=9813",
}


def test_complete_draft_is_classified_complete():
    out = classificar_rascunho(BASE)
    assert out["classe"] == "completo"
    assert out["motivos"] == []
    assert out["publicacao_autorizada"] is False


def test_missing_image_points_to_image_module():
    post = dict(BASE, featured_media=0)
    out = classificar_rascunho(post)
    assert out["classe"] == "incompleto"
    assert "featured_image_missing" in out["motivos"]
    assert "mkt_flow_p0.image_protocol" in out["responsaveis"]


def test_uncategorized_points_to_identity_module():
    post = dict(BASE, categories=[1])
    out = classificar_rascunho(post)
    assert "uncategorized_present" in out["motivos"]
    assert "mkt_flow_p0.editorial_identity" in out["responsaveis"]


def test_explicit_test_title_is_never_publishable():
    post = dict(BASE, title="[TESTE NAO PUBLICAR] exemplo")
    out = classificar_rascunho(post)
    assert out["classe"] == "de_teste"
    assert out["motivos"] == ["titulo_explicito_de_teste"]
    assert out["publicacao_autorizada"] is False


def test_content_missing_from_listing_is_not_a_false_blocker():
    # A listagem nao devolve content; nao pode ser contado como falta real.
    out = classificar_rascunho(BASE)
    assert "content_missing" not in out["motivos"]


def test_queue_aggregates_counts_without_approving():
    posts = [
        BASE,
        dict(BASE, id=9814, featured_media=0),
        dict(BASE, id=9633, title="[TESTE NAO PUBLICAR]"),
        dict(BASE, id=9815, categories=[1]),
    ]
    q = build_correction_queue(posts)
    assert q["total"] == 4
    assert q["contagens"]["completo"] == 1
    assert q["contagens"]["incompleto"] == 2
    assert q["contagens"]["de_teste"] == 1
    assert q["publicacao_autorizada"] is False


def test_invalid_post_fails_closed():
    out = classificar_rascunho(None)
    assert out["classe"] == "defasado"
    assert out["publicacao_autorizada"] is False
