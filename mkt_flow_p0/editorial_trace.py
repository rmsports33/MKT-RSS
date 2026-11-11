"""Trace envelope for the existing MKT-RSS handoff, no new publisher.

Returned in existing processar_item output and optionally in the existing
versioned handoff. It contains only operational metadata and digests.
This is NOT a factual approval or a WordPress publication receipt.
"""
import hashlib
import json
import uuid

SCHEMA = "conexo-editorial-executor-events/1"


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def make_trace(source_url, markdown, *, generated=None, readiness=None,
               post_id=None, wp_readback=False, error=None):
    if not isinstance(source_url, str) or not source_url.startswith("https://"):
        raise ValueError("invalid source URL")
    if not isinstance(markdown, str):
        raise ValueError("invalid markdown")
    generated = generated if isinstance(generated, dict) else {}
    content_sha = digest(markdown)
    article_id = "rss_" + digest(source_url)[:24]
    events = []
    def add(stage, module, status, evidence=None, error_code=None, model_id=None,
            prompt_sha=None):
        ev = {"stage": stage, "module_id": module, "module_version": "mkt-rss-trace/1",
              "status": status}
        if evidence:
            ev["evidence_ref"] = evidence
        if error_code:
            ev["error_code"] = error_code
        if model_id:
            ev["model_id"] = model_id
        if prompt_sha:
            ev["prompt_sha256"] = prompt_sha
        events.append(ev)

    if error:
        add("generation", "mkt-rss.groq", "FAIL", error_code="GENERATION_FAILED")
    elif generated.get("modelo") and generated.get("texto_markdown"):
        # Only the generation response is evidenced; no claim of factual or style review.
        add("generation", "mkt-rss.groq", "PASS",
            evidence="generated-text-sha256:" + digest(generated["texto_markdown"]),
            model_id=str(generated["modelo"])[:120],
            prompt_sha=generated.get("prompt_sha256"))
    else:
        add("generation", "mkt-rss.groq", "UNKNOWN")
    add("factual_review", "mkt-rss.editorial-readiness", "NOT_RUN")
    add("style_review", "mkt-rss.editorial-identity", "NOT_RUN")
    add("seo_review", "mkt-rss.seo-candidates", "UNKNOWN")
    if readiness and readiness.get("imagem_destacada_confirmada") is True:
        # This is readiness input only, not independent rights validation.
        add("image_review", "mkt-rss.image-candidates", "UNKNOWN")
    if post_id is not None:
        if type(post_id) is not int or post_id < 1:
            raise ValueError("invalid post id")
        add("delivery_readback", "mkt-rss.wp-draft-staging",
            "PASS" if wp_readback else "UNKNOWN",
            evidence="wp-post-id:" + str(post_id) if wp_readback else None)
    return {"schema": SCHEMA, "run_id": str(uuid.uuid4()), "article_id": article_id,
            "post_id": post_id, "content_sha256": content_sha,
            "events": events, "publication_authorized": False}


def json_trace(packet):
    return json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def save_trace(packet, handoff_dir):
    """Durable per-run sidecar with exclusive create; no content or secrets."""
    from pathlib import Path
    directory = Path(handoff_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ("trace-" + packet["run_id"] + ".json")
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json_trace(packet) + "\n")
    return str(path)
