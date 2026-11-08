"""Optional provenance preflight before the EXISTING canonical signed writer.

This is not another approval engine. It only ensures that a trusted readback
from the homologated Turso event store matches the exact package and contains
the review stages. The canonical editorial_write.prepare_write is still the
sole authority to sign a WordPress publication.
"""
import hashlib
import re
from mkt_flow_p0.editorial_trace_turso import get_turso_trace

REQUIRED = (
    "source_review", "research", "generation", "factual_review",
    "style_review", "seo_review", "image_review", "internal_links",
    "render_review", "editorial_approval",
)


def require_release_trace(package, run_id, *, lookup=get_turso_trace):
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", run_id):
        raise ValueError("trace_run_id_missing")
    if not isinstance(package, dict) or not isinstance(package.get("payload"), dict):
        raise ValueError("canonical_package_missing")
    payload = package["payload"]
    if not isinstance(payload.get("content"), str) or not payload["content"]:
        raise ValueError("canonical_content_missing")
    expected_hash = hashlib.sha256(payload["content"].encode("utf-8")).hexdigest()
    expected_article = payload.get("article_id")
    wp = payload.get("wordpress")
    expected_id = wp.get("post_id") if isinstance(wp, dict) else None
    reply = lookup(run_id)
    if not isinstance(reply, dict) or reply.get("ok") is not True:
        raise ValueError("trusted_trace_unavailable")
    packet = reply.get("trace")
    if (not isinstance(packet, dict)
            or packet.get("schema") != "conexo-editorial-executor-events/1"
            or packet.get("run_id") != run_id
            or packet.get("publication_authorized") is not False
            or packet.get("article_id") != expected_article
            or packet.get("post_id") != expected_id
            or packet.get("content_sha256") != expected_hash
            or not isinstance(packet.get("events"), list)):
        raise ValueError("editorial_trace_version_mismatch")
    latest = {}
    for event in packet["events"]:
        if (not isinstance(event, dict) or not isinstance(event.get("stage"), str)
                or not isinstance(event.get("status"), str)):
            raise ValueError("invalid_editorial_event")
        latest[event["stage"]] = event
    missing = [stage for stage in REQUIRED
               if latest.get(stage, {}).get("status") != "PASS"
               or not latest[stage].get("evidence_ref")]
    if missing:
        raise ValueError("editorial_trace_incomplete: " + ",".join(missing))
    # The trace is a precondition only; it cannot sign a publication.
    return {"trace_checked": True, "run_id": run_id,
            "content_sha256": expected_hash, "publication_authorized": False}
