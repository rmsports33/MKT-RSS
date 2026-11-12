"""MKT-RSS -> Conexo Gate RC2 broker, fail-closed and no exported HMAC.

Opt-in method. Never falls back to /wp/v2/posts or to the older
executor-side HMAC writer. The server WordPress broker signs internally
and invokes the canonical Gate, which enforces independent human approval.
The authorized Turso trace must exist and read back BEFORE WordPress POST.
"""
import hashlib
import json
import re
import requests
from pathlib import Path

from mkt_flow_p0.editorial_transport import SITE, load_core
from mkt_flow_p0.editorial_trace_gate import require_release_trace
from mkt_flow_p0.editorial_trace_turso import save_turso_trace

_SHA = re.compile(r"^[a-f0-9]{64}$")
_ALLOWED = {"publish": "publish", "schedule": "future"}


class BrokerBlocked(ValueError):
    pass


def _get_json(session, url, auth, timeout):
    try:
        response = session.get(url, auth=auth, timeout=timeout,
                               allow_redirects=False)
    except requests.RequestException as exc:
        raise BrokerBlocked("WP_READ_OUTCOME_UNKNOWN") from None
    if response.status_code != 200:
        raise BrokerBlocked("WP_READ_HTTP_REJECTED")
    try:
        value = response.json()
    except (ValueError, TypeError):
        raise BrokerBlocked("WP_READ_INVALID_JSON") from None
    if not isinstance(value, dict):
        raise BrokerBlocked("WP_READ_INVALID_BODY")
    return value


def publish_via_broker(package, *, core_root, wp_url, wp_user, wp_password,
                       trace_run_id, intent="publish", publication_reference=None,
                       post_date_gmt=None, trace_packet=None, timeout=15,
                       session=requests, require_signed_seo=False, owner_release=False):
    """One attempt, never automatically retry uncertain WordPress/Turso writes."""
    if not isinstance(wp_url, str) or wp_url.rstrip("/") != SITE:
        raise BrokerBlocked("WP_ORIGIN_NOT_ALLOWED")
    if not wp_user or not wp_password:
        raise BrokerBlocked("WP_SERVICE_ACCOUNT_NOT_CONFIGURED")
    if intent not in _ALLOWED:
        raise BrokerBlocked("BROKER_INTENT_DENIED")
    if not isinstance(publication_reference, str) or not (
            8 <= len(publication_reference) <= 200):
        raise BrokerBlocked("HUMAN_REFERENCE_MISSING")
    if not isinstance(package, dict) or not isinstance(package.get("payload"), dict):
        raise BrokerBlocked("CANONICAL_PACKAGE_INVALID")
    payload = package["payload"]
    wp = payload.get("wordpress")
    if not isinstance(wp, dict) or type(wp.get("post_id")) is not int or wp["post_id"] < 1:
        raise BrokerBlocked("WP_POST_ID_MISSING")
    post_id = wp["post_id"]
    version = package.get("version_sha256")
    if not isinstance(version, str) or not _SHA.fullmatch(version):
        raise BrokerBlocked("CANONICAL_VERSION_INVALID")

    # Retain the canonical validator from Conexo OS. Local PASS is not a
    # publication approval; the WP Gate independently checks review+quality.
    if owner_release:
        # Explicit proprietor mode uses the version-bound approval served by
        # the SAME WordPress Gate, never caller-supplied human PASS fields.
        trusted = _get_json(session, f"{SITE}/wp-json/conexo/v1/editorial/owner-release/{post_id}",
                            (wp_user, wp_password), timeout)
        owner_policy = (
            (intent == "publish" and require_signed_seo is True)
            or (intent == "schedule" and require_signed_seo is False)
        )
        # Existing canonical WP Gate protects future-post cron with a
        # version-and-date-bound receipt. Native SEO finalize is *not*
        # supported for future posts: schedule without claiming SEO finalized.
        if (trusted != package or trusted.get("schema") != "conexo-owner-release/1"
                or payload.get("owner_id") != 3 or payload.get("review_mode") != "owner"
                or payload.get("approval_reference") != publication_reference
                or not owner_policy):
            raise BrokerBlocked("OWNER_VERSION_NOT_AUTHENTICATED")
    else:
        core = load_core(core_root)
        validator = core.validator()
        problems, blocks = validator.evaluate(package, Path(core_root), for_staging=False)
        if problems or blocks:
            raise BrokerBlocked("CANONICAL_GATE_BLOCKED")

    if trace_packet is not None:
        if (not isinstance(trace_packet, dict) or
                trace_packet.get("run_id") != trace_run_id or
                trace_packet.get("post_id") != post_id):
            raise BrokerBlocked("TRACE_PACKET_MISMATCH")
        stored = save_turso_trace(trace_packet)
        if stored.get("ok") is not True:
            raise BrokerBlocked("TRACE_TURSO_STORE_NOT_CONFIRMED")
    # This existing validator fetches the authoritative Turso row and compares
    # content hash, post ID, article, PASS stages and evidence references.
    try:
        require_release_trace(package, trace_run_id)
    except (ValueError, TypeError, KeyError):
        raise BrokerBlocked("TRACE_TURSO_RELEASE_NOT_VERIFIED") from None

    auth = (wp_user, wp_password)
    seo_hash = None
    if require_signed_seo:
        seo = payload.get("seo")
        fields = ("provider", "canonical", "title", "description")
        if (not isinstance(seo, dict) or any(not isinstance(seo.get(k), str) or not seo[k].strip() for k in fields)
                or seo["provider"] != "native"):
            raise BrokerBlocked("BROKER_REVIEWED_SEO_MISSING")
        seo_hash = hashlib.sha256(json.dumps(
            {k: seo[k] for k in fields}, sort_keys=True, ensure_ascii=False,
            separators=(",", ":")).encode("utf-8")).hexdigest()
        ready = _get_json(session, f"{SITE}/wp-json/conexo/v1/editorial/seo-readiness", auth, timeout)
        if (ready.get("schema") != "conexo-seo-readiness/1" or any(ready.get(k) is not True for k in (
                "broker_signed_seo_supported", "editorial_gate_ready", "seo_signing_ready", "seo_public_output_ready"))):
            raise BrokerBlocked("BROKER_SIGNED_SEO_NOT_READY")
    snap = _get_json(session, f"{SITE}/wp-json/conexo/v1/editorial/snapshot/{post_id}",
                     auth, timeout)
    current = snap.get("snapshot")
    sha = snap.get("snapshot_sha256")
    if (not isinstance(current, dict) or current.get("ID") != post_id or
            current.get("post_status") not in ("draft", "pending") or
            not isinstance(sha, str) or not _SHA.fullmatch(sha)):
        raise BrokerBlocked("WP_SNAPSHOT_NOT_EDITABLE")
    article = payload.get("content")
    if (not isinstance(article, str) or
            hashlib.sha256(article.encode("utf-8")).hexdigest() !=
            hashlib.sha256(str(current.get("post_content", "")).encode("utf-8")).hexdigest()):
        raise BrokerBlocked("WP_CONTENT_MISMATCH")
    expected = {
        "executor": "mkt_rss", "post_id": post_id, "intent": intent,
        "expected_sha256": sha, "version_sha256": version,
        "publication_reference": publication_reference,
    }
    if require_signed_seo:
        if intent != "publish":
            raise BrokerBlocked("BROKER_SIGNED_SEO_INTENT_DENIED")
        expected.update(require_signed_seo=True, seo_sha256=seo_hash)
    if intent == "schedule":
        if not isinstance(post_date_gmt, str) or not re.fullmatch(
                r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", post_date_gmt):
            raise BrokerBlocked("SCHEDULE_GMT_INVALID")
        expected["post_date_gmt"] = post_date_gmt
    elif post_date_gmt is not None:
        raise BrokerBlocked("SCHEDULE_GMT_UNEXPECTED")

    try:
        response = session.post(f"{SITE}/wp-json/conexo/v1/editorial/broker/write",
                                json=expected, auth=auth, timeout=timeout,
                                allow_redirects=False)
    except requests.RequestException:
        raise BrokerBlocked("BROKER_OUTCOME_UNKNOWN_RECONCILE_NO_RETRY") from None
    if response.status_code not in (200, 201):
        raise BrokerBlocked("BROKER_REJECTED_NO_RETRY")
    try:
        result = response.json()
    except (ValueError, TypeError):
        raise BrokerBlocked("BROKER_RESULT_INVALID") from None
    if (not isinstance(result, dict) or result.get("post_id") != post_id or
            result.get("version_sha256") != version or
            result.get("intent") != intent or
            result.get("status") != _ALLOWED[intent]):
        raise BrokerBlocked("BROKER_READBACK_NOT_VERIFIED")

    # Re-read exact post status from the authenticated Gate route.
    observed = _get_json(session,
                         f"{SITE}/wp-json/conexo/v1/editorial/snapshot/{post_id}",
                         auth, timeout).get("snapshot")
    if not isinstance(observed, dict) or observed.get("ID") != post_id or (
            observed.get("post_status") != _ALLOWED[intent]):
        raise BrokerBlocked("BROKER_REMOTE_STATUS_MISMATCH")
    if require_signed_seo:
        if observed != result.get("snapshot"):
            raise BrokerBlocked("BROKER_REMOTE_SNAPSHOT_MISMATCH_NO_RETRY")
        if (result.get("publicacao_seo_concluidos") is not True
                or not isinstance(result.get("seo_private_delivery"), dict)
                or result["seo_private_delivery"].get("status") != "verified"):
            return {"erro": "publicacao confirmada; SEO pendente de inspecao",
                    "post_id": post_id, "nonce": result.get("nonce"),
                    "publicacao_seo_concluidos": False, "retry_automatic": False}
    out = {"verified": True, "post_id": post_id, "intent": intent,
            "version_sha256": version, "trace_run_id": trace_run_id, "retry_automatic": False}
    if require_signed_seo:
        out["publicacao_seo_concluidos"] = True
    return out
