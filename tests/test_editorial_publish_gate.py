from editorial_publish_gate import (
    _matches_canonical_package_snapshot,
    authorize_publish,
    require_publish_authorization,
)
import pytest
from mkt_flow_p0.editorial_provenance import MODULOS_OBRIGATORIOS, marcar

POST = {"id": 123, "status": "draft", "categories": [10],
        "slug": "noticia-verificada", "featured_media": 456,
        "title": "Notícia verificada", "content": "<p>Texto confirmado</p>",
        "link": "https://conexotech.com.br/?p=123"}
REVIEW = {"veredito": "APROVADO", "revisao_substantiva": True,
          "evidencias_verificadas": True, "aprovacao_atual": True}


def corpo_com_proveniencia(**overrides):
    values = dict(
        modules={name: "EXECUTED" for name in MODULOS_OBRIGATORIOS},
        voice_status="ASSISTED_ADAPTED",
        substance_status="PASS",
        image_rights_confirmed=True,
        version_sha256="a" * 64,
    )
    values.update(overrides)
    return marcar("<p>Texto confirmado</p>", **values)[0]


def test_four_flags_do_not_replace_canonical_package():
    assert not authorize_publish(POST, REVIEW)["autorizado"]
    assert "trusted_factual_review_missing" in authorize_publish(POST, REVIEW)["bloqueios"]
    with pytest.raises(PermissionError):
        require_publish_authorization(POST, REVIEW)


@pytest.mark.parametrize("key,value", [
    ("veredito", "SEM_ALERTAS"),
    ("revisao_substantiva", False),
    ("evidencias_verificadas", False),
    ("aprovacao_atual", False),
])
def test_factual_gate_fails_closed(key, value):
    result = authorize_publish(POST, {**REVIEW, key: value})
    assert not result["autorizado"]
    with pytest.raises(PermissionError):
        require_publish_authorization(POST, {**REVIEW, key: value})


def test_missing_factual_review():
    assert "canonical_editorial_package_missing" in authorize_publish(POST, None)["bloqueios"]


def test_media_missing_even_with_approved_facts():
    result = authorize_publish({**POST, "featured_media": 0}, REVIEW)
    assert "featured_image_missing" in result["bloqueios"]


def test_published_post_is_not_valid_transition_source():
    assert not authorize_publish({**POST, "status": "publish"}, REVIEW)["autorizado"]


def test_missing_review_fails_closed():
    assert "factual_review_missing" in authorize_publish(POST, None)["bloqueios"]


def test_missing_core_blocks_publication():
    result = authorize_publish(
        POST, REVIEW,
        package={"stage": "ready", "payload": {}},
        core_root="/missing-conexo-editorial-core-for-regression",
    )
    assert result["autorizado"] is False
    assert "canonical_gate_unavailable_or_invalid" in result["bloqueios"]


def test_missing_provenance_marker_blocks_even_before_owner_gate():
    result = authorize_publish(POST, REVIEW)
    assert result["autorizado"] is False
    assert "editorial_provenance_marca_ausente" in result["bloqueios"]


def test_invalid_provenance_marker_blocks_fail_closed():
    bad = {**POST, "content": "<p>Alterado depois da marca</p>" + corpo_com_proveniencia()}
    result = authorize_publish(bad, REVIEW)
    assert result["autorizado"] is False
    assert any(item.startswith("editorial_provenance_") for item in result["bloqueios"])


def test_valid_provenance_does_not_replace_owner_release_or_canonical_package():
    marked = {**POST, "content": corpo_com_proveniencia()}
    result = authorize_publish(marked, REVIEW)
    assert result["autorizado"] is False
    assert not any(item.startswith("editorial_provenance_") for item in result["bloqueios"])
    assert "gate_owner_release_missing" in result["bloqueios"]
    assert "canonical_editorial_package_missing" in result["bloqueios"]


def test_rest_content_requires_raw_not_only_rendered():
    rest_post = {**POST, "content": {"rendered": corpo_com_proveniencia()}}
    result = authorize_publish(rest_post, REVIEW)
    assert result["autorizado"] is False
    assert "editorial_provenance_content_raw_unavailable" in result["bloqueios"]


def test_rest_edit_objects_use_raw_not_rendered_for_readiness():
    raw = corpo_com_proveniencia()
    rest_post = {
        **POST,
        "title": {"raw": "Notícia verificada", "rendered": "Título renderizado divergente"},
        "content": {"raw": raw, "rendered": "<p>HTML renderizado diferente</p>"},
    }
    result = authorize_publish(rest_post, REVIEW)
    assert result["autorizado"] is False
    assert not any(item.startswith("editorial_provenance_") for item in result["bloqueios"])
    assert "content_missing" not in result["bloqueios"]
    assert "title_missing" not in result["bloqueios"]


def test_rest_rendered_only_title_is_not_accepted_as_version_source():
    rest_post = {
        **POST,
        "title": {"rendered": "Título apenas renderizado"},
        "content": {"raw": corpo_com_proveniencia(), "rendered": "<p>Body</p>"},
    }
    result = authorize_publish(rest_post, REVIEW)
    assert result["autorizado"] is False
    assert "title_missing" in result["bloqueios"]


def test_canonical_package_snapshot_matches_raw_rest_content():
    raw = corpo_com_proveniencia()
    payload = {
        "title": POST["title"],
        "slug": POST["slug"],
        "content": raw,
        "wordpress": {
            "post_id": POST["id"],
            "featured_media": POST["featured_media"],
            "categories": POST["categories"],
        },
    }
    rest_post = {
        **POST,
        "title": {"raw": POST["title"], "rendered": "Rendered title can differ"},
        "content": {"raw": raw, "rendered": "<p>Rendered HTML can differ</p>"},
    }
    assert _matches_canonical_package_snapshot(rest_post, payload) is True


def test_canonical_package_snapshot_rejects_rendered_only_content():
    raw = corpo_com_proveniencia()
    payload = {
        "title": POST["title"],
        "slug": POST["slug"],
        "content": raw,
        "wordpress": {
            "post_id": POST["id"],
            "featured_media": POST["featured_media"],
            "categories": POST["categories"],
        },
    }
    rest_post = {
        **POST,
        "title": {"raw": POST["title"], "rendered": POST["title"]},
        "content": {"rendered": raw},
    }
    assert _matches_canonical_package_snapshot(rest_post, payload) is False
