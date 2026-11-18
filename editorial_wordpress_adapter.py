"""Supervised, read-only WordPress draft inspection and HTML readback verification.

Does not publish or change a draft. The fetch callable is injected so tests
cannot accidentally connect to production. Boolean editorial flags alone
cannot authorize publishing.
"""
import hashlib
import json
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

from editorial_publish_gate import authorize_publish
from mkt_flow_p0.editorial_provenance import validar_integridade


_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


class _VideoMarkupParser(HTMLParser):
    """Collect only YouTube no-cookie embeds and VideoObject JSON-LD."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.iframe_ids = []
        self.schema_ids = []
        self.invalid = []
        self._script_parts = None

    @staticmethod
    def _video_id(url):
        if not isinstance(url, str):
            return None
        try:
            parsed = urlsplit(url)
        except ValueError:
            return None
        match = re.fullmatch(r"/embed/([A-Za-z0-9_-]{11})", parsed.path)
        if (parsed.scheme != "https"
                or parsed.hostname not in {"youtube-nocookie.com", "www.youtube-nocookie.com"}
                or parsed.username or parsed.password or parsed.port not in (None, 443)
                or match is None):
            return None
        return match.group(1)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "iframe":
            src = values.get("src")
            video_id = self._video_id(src)
            if video_id is None:
                self.invalid.append("iframe")
            else:
                self.iframe_ids.append(video_id)
        elif tag == "script" and str(values.get("type", "")).lower() == "application/ld+json":
            self._script_parts = []

    def handle_data(self, data):
        if self._script_parts is not None:
            self._script_parts.append(data)

    def handle_endtag(self, tag):
        if tag != "script" or self._script_parts is None:
            return
        raw = "".join(self._script_parts)
        self._script_parts = None
        try:
            value = json.loads(raw)
        except (TypeError, ValueError):
            if "VideoObject" in raw:
                self.invalid.append("jsonld")
            return
        values = value if isinstance(value, list) else [value]
        for item in values:
            if not isinstance(item, dict) or item.get("@type") != "VideoObject":
                continue
            video_id = self._video_id(item.get("embedUrl"))
            if video_id is None:
                self.invalid.append("videoobject")
            else:
                self.schema_ids.append(video_id)


def _video_markup_summary(content):
    parser = _VideoMarkupParser()
    try:
        parser.feed(content or "")
        parser.close()
    except Exception:
        return {"iframe_ids": [], "schema_ids": [], "invalid": ["html"]}
    return {
        "iframe_ids": parser.iframe_ids,
        "schema_ids": parser.schema_ids,
        "invalid": parser.invalid,
    }


def _context_content(post, field):
    """Read the content string supplied by one explicitly requested REST context."""
    content = post.get("content") if isinstance(post, dict) else None
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        value = content.get(field)
        return value if isinstance(value, str) else None
    return None


def assemble_wordpress_context_readback(edit_post, view_post):
    """Pair separate context=edit (raw) and context=view (rendered) GET results.

    The connector used by ConexoTech flattens each REST context to a string.
    Pairing is safe only when both reads refer to the same post version and
    status. A single flattened string is never promoted to raw+rendered.
    """
    if not isinstance(edit_post, dict) or not isinstance(view_post, dict):
        return None, ["wordpress_context_response_invalid"]

    edit_id = edit_post.get("id")
    view_id = view_post.get("id")
    if (type(edit_id) is not int or edit_id <= 0
            or type(view_id) is not int or view_id != edit_id):
        return None, ["wordpress_context_post_id_mismatch"]

    edit_modified = edit_post.get("modified")
    view_modified = view_post.get("modified")
    if (not isinstance(edit_modified, str) or not edit_modified.strip()
            or edit_modified != view_modified):
        return None, ["wordpress_context_version_mismatch"]

    edit_status = edit_post.get("status")
    view_status = view_post.get("status")
    if (not isinstance(edit_status, str) or not edit_status.strip()
            or edit_status != view_status):
        return None, ["wordpress_context_status_mismatch"]

    raw = _context_content(edit_post, "raw")
    rendered = _context_content(view_post, "rendered")
    if not isinstance(raw, str) or not raw.strip():
        return None, ["wordpress_content_raw_unavailable"]
    if not isinstance(rendered, str) or not rendered.strip():
        return None, ["wordpress_rendered_content_unavailable"]

    combined = dict(edit_post)
    combined["content"] = {"raw": raw, "rendered": rendered}
    return combined, []


def validate_wordpress_content_readback(post):
    """Verify stored raw-body integrity and that rendered HTML retained video markup.

    Requires both content.raw and content.rendered from edit context. A flattened
    connector string is inconclusive, not raw. When raw contains a video, rendered
    must retain the matching iframe and VideoObject schema. This is read-only.
    """
    if not isinstance(post, dict):
        return {"valid": False, "blockers": ["wordpress_response_invalid"]}
    content = post.get("content")
    if isinstance(content, dict):
        raw = content.get("raw")
        rendered = content.get("rendered")
    else:
        # A connector's flattened content string is not proof of raw storage.
        raw = None
        rendered = None
    blockers = []
    if not isinstance(raw, str) or not raw.strip():
        return {"valid": False, "blockers": ["wordpress_content_raw_unavailable"]}
    if not isinstance(rendered, str) or not rendered.strip():
        blockers.append("wordpress_rendered_content_unavailable")
    integrity = validar_integridade(raw)
    if not integrity["valido"]:
        blockers.append("wordpress_raw_provenance_" + integrity.get("motivo", "invalid"))
    raw_video = _video_markup_summary(raw)
    if raw_video["invalid"]:
        blockers.append("wordpress_raw_video_markup_invalid")
    if raw_video["iframe_ids"] != raw_video["schema_ids"]:
        if raw_video["iframe_ids"] or raw_video["schema_ids"]:
            blockers.append("wordpress_raw_video_markup_incomplete")
    if isinstance(rendered, str) and rendered.strip():
        rendered_video = _video_markup_summary(rendered)
        if rendered_video["invalid"]:
            blockers.append("wordpress_rendered_video_markup_invalid")
        if raw_video["iframe_ids"]:
            if (rendered_video["iframe_ids"] != raw_video["iframe_ids"]
                    or rendered_video["schema_ids"] != raw_video["schema_ids"]):
                blockers.append("wordpress_rendered_video_markup_changed")
        elif rendered_video["iframe_ids"] or rendered_video["schema_ids"]:
            blockers.append("wordpress_rendered_video_markup_unexpected")
    return {
        "valid": not blockers,
        "blockers": list(dict.fromkeys(blockers)),
        "content_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "video_ids": raw_video["iframe_ids"],
    }


def inspect_wordpress_draft(fetch_post, post_id, factual_review,
                            *, expected_category_id=10, fetch_post_view=None):
    if type(post_id) is not int or post_id <= 0:
        return {"authorized": False, "blockers": ["post_id_invalid"], "post": None}
    if not callable(fetch_post):
        return {"authorized": False, "blockers": ["fetch_post_missing"], "post": None}
    try:
        data = fetch_post(post_id)
        if fetch_post_view is not None:
            if not callable(fetch_post_view):
                return {"authorized": False, "blockers": ["fetch_post_view_missing"], "post": None}
            edit_data = data
            view_data = fetch_post_view(post_id)
            data, context_blockers = assemble_wordpress_context_readback(edit_data, view_data)
            if context_blockers:
                return {
                    "authorized": False,
                    "blockers": context_blockers,
                    "readback_valid": False,
                    "readback_blockers": context_blockers,
                    "post": {
                        "id": post_id,
                        "status": edit_data.get("status") if isinstance(edit_data, dict) else None,
                    },
                }
    except Exception:
        return {"authorized": False, "blockers": ["wordpress_read_failed"], "post": None}
    if not isinstance(data, dict) or type(data.get("id")) is not int or data["id"] != post_id:
        return {"authorized": False, "blockers": ["wordpress_response_invalid"], "post": None}
    # Preserve the REST objects: authorize_publish extracts raw explicitly,
    # while readback validation independently requires raw and rendered.
    post = dict(data)
    result = authorize_publish(post, factual_review,
                               expected_category_id=expected_category_id)
    readback = validate_wordpress_content_readback(data)
    blockers = list(dict.fromkeys(result["bloqueios"] + readback["blockers"]))
    return {"authorized": not blockers,
            "blockers": blockers,
            "readback_valid": readback["valid"],
            "readback_blockers": readback["blockers"],
            "post": {"id": post_id, "status": post.get("status")}}
