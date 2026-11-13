"""Conexo Gate trace transport for authenticated MKT-RSS executor.

Call send_after_wordpress_draft() ONLY after the real MKT-RSS run finishes
and the resulting draft is persisted. It does not approve, schedule or publish.
No GitHub Actions or credentials stored in this module.
"""
import base64
import hashlib
import json
import os
import re
from urllib.request import Request, urlopen

SITE = "https://conexotech.com.br"
STAGES = ("rss_collect", "source_verify", "topic_intent", "draft_dna",
          "fact_check", "style_review", "seo_prepare", "image_license",
          "links_verify", "html_check", "visual_preview")
VALID = {"PASS", "FAIL", "SKIPPED", "NOT_RUN", "UNKNOWN"}


class TraceBlocked(ValueError):
    pass


def validate_manifest(manifest):
    if not isinstance(manifest, dict):
        raise TraceBlocked("Manifest is not an object")
    run_id = manifest.get("run_id")
    post_id = manifest.get("post_id")
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", run_id):
        raise TraceBlocked("Invalid run_id")
    if type(post_id) is not int or post_id < 1:
        raise TraceBlocked("Invalid post_id")
    entries = manifest.get("events")
    if not isinstance(entries, list) or len(entries) != len(STAGES):
        raise TraceBlocked("Eleven real stage events are required")
    found = {}
    for event in entries:
        if not isinstance(event, dict) or event.get("stage") not in STAGES:
            raise TraceBlocked("Unknown stage")
        stage = event["stage"]
        if stage in found or event.get("status") not in VALID:
            raise TraceBlocked("Duplicate stage or invalid status")
        for field in ("module_id", "module_version", "evidence_ref"):
            value = event.get(field)
            if not isinstance(value, str) or len(value) < 2:
                raise TraceBlocked("Missing evidence field: " + field)
        if (type(event.get("started_at")) is not int or
            type(event.get("ended_at")) is not int or
            event["ended_at"] < event["started_at"]):
            raise TraceBlocked("Invalid stage times")
        found[stage] = event
    return run_id, post_id, found


def send_after_wordpress_draft(manifest, *, transport=None):
    """Run at the real post-persist completion hook; never manufacture PASS."""
    run_id, post_id, events = validate_manifest(manifest)
    if transport is None:
        username = os.environ.get("CONEXO_WP_USER")
        password = os.environ.get("CONEXO_WP_APP_PASSWORD")
        if not username or not password:
            raise TraceBlocked("MKT-RSS service credentials are not configured")
        auth = "Basic " + base64.b64encode((username + ":" + password).encode()).decode()

        def transport(method, path, data=None):
            raw = None if data is None else json.dumps(data, ensure_ascii=False).encode()
            req = Request(SITE + path, data=raw, method=method,
                          headers={"Authorization": auth, "Content-Type": "application/json"})
            with urlopen(req, timeout=20) as reply:
                return json.load(reply)

    post = transport("GET", "/wp-json/wp/v2/posts/%d?context=edit" % post_id)
    if post.get("status") not in ("draft", "pending"):
        raise TraceBlocked("Article is not an editable draft")
    body = post.get("content", {}).get("raw")
    if not isinstance(body, str):
        raise TraceBlocked("Raw content not available")
    digest = hashlib.sha256(body.encode()).hexdigest()
    if digest != manifest.get("content_sha256"):
        raise TraceBlocked("Draft content and trace version differ")
    reply = transport("POST", "/wp-json/conexo/v1/editorial/trace/bind",
                      {"post_id": post_id, "run_id": run_id, "content_sha256": digest})
    if reply.get("bound") is not True:
        raise TraceBlocked("Gate did not confirm trace binding")
    for stage in STAGES:
        event = {**events[stage], "schema": "conexo-editorial-trace/1",
                 "run_id": run_id, "post_id": post_id, "content_sha256": digest}
        answer = transport("POST", "/wp-json/conexo/v1/editorial/trace/event", event)
        if answer.get("recorded") is not True:
            raise TraceBlocked("Gate did not confirm event " + stage)
    return {"post_id": post_id, "run_id": run_id, "recorded": len(STAGES),
            "all_pass": all(events[stage]["status"] == "PASS" for stage in STAGES)}
