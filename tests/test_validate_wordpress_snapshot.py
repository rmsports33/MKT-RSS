from tools.validate_wordpress_snapshot import validate_snapshot
from mkt_flow_p0.editorial_provenance import MODULOS_OBRIGATORIOS, marcar
from mkt_flow_p0.editorial_video import bloco_video, videoobject_jsonld


VIDEO = {"youtube_id": "dQw4w9WgXcQ", "titulo": "Review real", "canal": "Canal real"}


def _snapshot():
    body = marcar(
        "<h2>Review</h2>\n" + bloco_video(VIDEO) + "\n" + videoobject_jsonld(VIDEO),
        modules={name: "EXECUTED" for name in MODULOS_OBRIGATORIOS},
        voice_status="ASSISTED_ADAPTED",
        substance_status="PASS",
        image_rights_confirmed=True,
        version_sha256="b" * 64,
    )[0]
    base = {
        "id": 42,
        "status": "draft",
        "modified": "2026-11-18T09:00:00",
        "content": {"raw": body, "rendered": body},
    }
    return {"edit_post": base, "view_post": base}


def test_saved_snapshot_validates_without_wordpress_or_credentials():
    result = validate_snapshot(_snapshot())
    assert result["valid"] is True
    assert result["blockers"] == []
    assert result["post_id"] == 42
    assert result["video_ids"] == ["dQw4w9WgXcQ"]
    assert "raw_sha256" in result and "rendered_sha256" in result
    assert "Review</h2>" not in str(result)


def test_saved_snapshot_rejects_different_wordpress_versions():
    snapshot = _snapshot()
    snapshot["view_post"] = {
        **snapshot["view_post"],
        "modified": "2026-11-18T09:01:00",
    }
    result = validate_snapshot(snapshot)
    assert result["valid"] is False
    assert result["blockers"] == ["wordpress_context_version_mismatch"]


def test_saved_snapshot_rejects_missing_raw_content():
    snapshot = _snapshot()
    snapshot["edit_post"] = {
        **snapshot["edit_post"],
        "content": {"rendered": snapshot["edit_post"]["content"]["rendered"]},
    }
    result = validate_snapshot(snapshot)
    assert result["valid"] is False
    assert result["blockers"] == ["wordpress_content_raw_unavailable"]
