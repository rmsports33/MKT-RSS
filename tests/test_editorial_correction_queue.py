"""MKT-RSS #114: fila de correção derivada de metadados WordPress."""
from mkt_flow_p0.editorial_correction_queue import (
    classificar_rascunho, build_correction_queue)

BASE = {
    "id": 9813, "status": "draft", "slug": "noticia-verificada",
    "categories": [10], "featured_media": 456,
    "title": "Notícia verificada sobre tecnologia",
    "link": "https://conexotech.com.br/?p=9813",
}


def test_complete_draft_is_classified_complete():
    out = classificar_rascunho(BASE)
    assert out["classe"] == "completo"
    assert out["motivos"] == []
    assert out["publicacao_autorizada"] is False


def test_wordpress_list_rendered_title_is_normalized():
    post = dict(BASE, title={"rendered": "Notícia verificada sobre tecnologia"})
    out = classificar_rascunho(post)
    assert out["classe"] == "completo"
    assert "title_missing" not in out["motivos"]
    assert isinstance(post["title"], dict)  # input remains untouched


def test_wordpress_edit_raw_title_is_normalized():
    post = dict(BASE, title={"raw": "Notícia verificada sobre tecnologia"})
    out = classificar_rascunho(post)
    assert out["classe"] == "completo"
    assert "title_missing" not in out["motivos"]


def test_missing_or_malformed_title_fails_closed():
    for title in (None, {}, {"rendered": None, "raw": None}):
        out = classificar_rascunho(dict(BASE, title=title))
        assert out["classe"] == "incompleto"
        assert "title_missing" in out["motivos"]


def test_rendered_test_title_is_never_publishable():
    post = dict(BASE, title={"rendered": "[TESTE NAO PUBLICAR] exemplo"})
    out = classificar_rascunho(post)
    assert out["classe"] == "de_teste"
    assert out["publicacao_autorizada"] is False


def test_missing_image_points_to_image_module():
    out = classificar_rascunho(dict(BASE, featured_media=0))
    assert out["classe"] == "incompleto"
    assert "featured_image_missing" in out["motivos"]
    assert "mkt_flow_p0.image_protocol" in out["responsaveis"]


def test_uncategorized_points_to_identity_module():
    out = classificar_rascunho(dict(BASE, categories=[1]))
    assert "uncategorized_present" in out["motivos"]
    assert "mkt_flow_p0.editorial_identity" in out["responsaveis"]


def test_explicit_test_title_is_never_publishable():
    out = classificar_rascunho(dict(BASE, title="[TESTE NAO PUBLICAR] exemplo"))
    assert out["classe"] == "de_teste"
    assert out["motivos"] == ["titulo_explicito_de_teste"]
    assert out["publicacao_autorizada"] is False


def test_content_missing_from_listing_is_not_a_false_blocker():
    out = classificar_rascunho(BASE)
    assert "content_missing" not in out["motivos"]


def test_queue_aggregates_counts_without_approving():
    posts = [BASE, dict(BASE, id=9814, featured_media=0),
             dict(BASE, id=9633, title={"rendered": "[TESTE NAO PUBLICAR]"}),
             dict(BASE, id=9815, categories=[1])]
    queue = build_correction_queue(posts)
    assert queue["total"] == 4
    assert queue["contagens"]["completo"] == 1
    assert queue["contagens"]["incompleto"] == 2
    assert queue["contagens"]["de_teste"] == 1
    assert queue["publicacao_autorizada"] is False


def test_invalid_post_fails_closed():
    out = classificar_rascunho(None)
    assert out["classe"] == "defasado"
    assert out["publicacao_autorizada"] is False
