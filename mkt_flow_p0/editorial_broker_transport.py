"""MKT-RSS -> Conexo Gate RC2 broker, fail-closed and no exported HMAC.

Opt-in method. Never falls back to /wp/v2/posts or to the older
executor-side HMAC writer. The server WordPress broker signs internally
and invokes the canonical Gate, which enforces independent human approval.
The authorized Turso trace must exist and read back BEFORE WordPress POST.
"""
import hashlib
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
                       session=requests):
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
    return {"verified": True, "post_id": post_id, "intent": intent,
            "trace_run_id": trace_run_id, "retry_automatic": False}
