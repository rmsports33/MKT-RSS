from editorial_wordpress_adapter import (
    inspect_wordpress_draft,
    validate_wordpress_content_readback,
)
from mkt_flow_p0.editorial_provenance import MODULOS_OBRIGATORIOS, marcar
from mkt_flow_p0.editorial_video import bloco_video, videoobject_jsonld

REVIEW = {"veredito": "APROVADO", "revisao_substantiva": True,
          "evidencias_verificadas": True, "aprovacao_atual": True}


def marked_body(content):
    return marcar(
        content,
        modules={name: "EXECUTED" for name in MODULOS_OBRIGATORIOS},
        voice_status="ASSISTED_ADAPTED",
        substance_status="PASS",
        image_rights_confirmed=True,
        version_sha256="b" * 64,
    )[0]


BODY = marked_body("<p>Conteudo persistido.</p>")
DRAFT = {
    "id": 42, "status": "draft", "categories": [10],
    "slug": "noticia", "featured_media": 21,
    "title": {"raw": "Noticia", "rendered": "Noticia"},
    "content": {"raw": BODY, "rendered": BODY},
    "link": "https://conexotech.com.br/?p=42",
}
VIDEO = {
    "youtube_id": "dQw4w9WgXcQ",
    "titulo": "Review real",
    "canal": "Canal real",
}
VIDEO_BODY = marked_body(
    "<h2>Review</h2>\n"
    + bloco_video(VIDEO) + "\n"
    + videoobject_jsonld(VIDEO)
)
VIDEO_DRAFT = {
    **DRAFT,
    "content": {"raw": VIDEO_BODY, "rendered": VIDEO_BODY},
}


def test_reads_persisted_draft_but_blocks_uncertified_review():
    calls = []
    result = inspect_wordpress_draft(lambda post_id: (calls.append(post_id), DRAFT)[1],
                                      42, REVIEW)
    assert calls == [42]
    assert not result["authorized"]
    assert result["readback_valid"] is True
    assert "trusted_factual_review_missing" in result["blockers"]


def test_bad_id_prevents_fetch():
    def forbidden(_):
        raise AssertionError("Must not fetch")
    result = inspect_wordpress_draft(forbidden, True, REVIEW)
    assert not result["authorized"]
    assert result["blockers"] == ["post_id_invalid"]


def test_failed_fetch_blocks():
    def failing(_):
        raise ConnectionError("unavailable")
    assert "wordpress_read_failed" in inspect_wordpress_draft(failing, 42, REVIEW)["blockers"]


def test_wrong_post_id_blocks():
    assert "wordpress_response_invalid" in inspect_wordpress_draft(
        lambda _: {**DRAFT, "id": 43}, 42, REVIEW)["blockers"]


def test_malformed_status_blocks():
    result = inspect_wordpress_draft(lambda _: {**DRAFT, "status": "publish"}, 42, REVIEW)
    assert not result["authorized"]
    assert "unexpected_status" in result["blockers"]


def test_wordpress_readback_confirms_raw_hash_and_video_objects():
    result = validate_wordpress_content_readback(VIDEO_DRAFT)
    assert result["valid"] is True
    assert result["blockers"] == []
    assert result["video_ids"] == ["dQw4w9WgXcQ"]


def test_readback_detects_wordpress_stripping_iframe_or_schema():
    rendered_without_iframe = VIDEO_BODY.replace(
        '<iframe src="https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?rel=0"',
        '<div data-sanitized="iframe-removed"')
    result = validate_wordpress_content_readback({
        **VIDEO_DRAFT,
        "content": {"raw": VIDEO_BODY, "rendered": rendered_without_iframe},
    })
    assert result["valid"] is False
    assert "wordpress_rendered_video_markup_changed" in result["blockers"]


def test_readback_detects_jsonld_removed_after_save():
    rendered_without_schema = VIDEO_BODY.replace(videoobject_jsonld(VIDEO), "")
    result = validate_wordpress_content_readback({
        **VIDEO_DRAFT,
        "content": {"raw": VIDEO_BODY, "rendered": rendered_without_schema},
    })
    assert result["valid"] is False
    assert "wordpress_rendered_video_markup_changed" in result["blockers"]


def test_readback_requires_raw_content_not_only_rendered():
    result = validate_wordpress_content_readback({
        **DRAFT,
        "content": {"rendered": BODY},
    })
    assert result["valid"] is False
    assert result["blockers"] == ["wordpress_content_raw_unavailable"]


def test_readback_detects_mutation_of_persisted_raw_content():
    mutated = VIDEO_BODY.replace("Review real", "Review alterado", 1)
    result = validate_wordpress_content_readback({
        **VIDEO_DRAFT,
        "content": {"raw": mutated, "rendered": mutated},
    })
    assert result["valid"] is False
    assert "wordpress_raw_provenance_hash_divergente" in result["blockers"]



def test_readback_rejects_flattened_connector_content_string():
    result = validate_wordpress_content_readback({
        **DRAFT,
        "content": BODY,
    })
    assert result["valid"] is False
    assert result["blockers"] == ["wordpress_content_raw_unavailable"]


def test_readback_requires_rendered_content_even_without_video():
    result = validate_wordpress_content_readback({
        **DRAFT,
        "content": {"raw": BODY},
    })
    assert result["valid"] is False
    assert "wordpress_rendered_content_unavailable" in result["blockers"]
