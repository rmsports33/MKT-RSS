"""One-time native WordPress scheduling of six genuinely Gate-approved drafts.

Consumes WordPress Gate owner-release receipts from the authenticated editor 4.
No GitHub cron or publication per post: six future posts are scheduled once.
Never fabricates owner decisions, never uses wp/v2 POST to bypass the Gate.

Important: the currently installed broker does not finalize Conexo Native SEO
at scheduling time; reviewed SEO is persisted in Gate but signed Native SEO
finalization for future posts requires separate WP implementation/verification.
"""
import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

from mkt_flow_p0.editorial_broker_transport import (
    BrokerBlocked, _get_json, publish_via_broker,
)
from mkt_flow_p0.editorial_transport import SITE
from tools.publish_owner_approved import owner_trace
from tools.wp_identity_preflight import check_identity

TIMEZONE = ZoneInfo("America/Fortaleza")
# A related-article launch cluster; keep future titles readable in the posts.
POSTS = (
    (9813, 9839),  # Tesla Optimus, industrial update
    (9815, 9841),  # Optimus vs Unitree G1
    (9814, 9840),  # Unitree R1/G1 import guide
    (9810, 9838),  # 1X NEO contractual analysis
    (9816, 9842),  # Figure 03
    (9817, 9843),  # LG CLOiD
)


def _site_post(post_id, session):
    auth = (os.environ["WP_USER"], os.environ["WP_APP_PASSWORD"])
    return _get_json(
        session, f"{SITE}/wp-json/wp/v2/posts/{post_id}?context=edit",
        auth, 15,
    )


def _owner_receipt(post_id, session):
    auth = (os.environ["WP_USER"], os.environ["WP_APP_PASSWORD"])
    return _get_json(
        session, f"{SITE}/wp-json/conexo/v1/editorial/owner-release/{post_id}",
        auth, 15,
    )


def _start_at(local_iso, now):
    if not isinstance(local_iso, str) or not re.fullmatch(
            r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}", local_iso):
        raise BrokerBlocked("INVALID_LOCAL_DATETIME")
    try:
        start = datetime.strptime(local_iso, "%Y-%m-%dT%H:%M").replace(
            tzinfo=TIMEZONE
        )
    except ValueError:
        raise BrokerBlocked("INVALID_LOCAL_DATETIME") from None
    if now.tzinfo is None or start.astimezone(timezone.utc) < (
            now.astimezone(timezone.utc) + timedelta(minutes=10)):
        raise BrokerBlocked("SCHEDULE_START_MUST_BE_TEN_MINUTES_AHEAD")
    return start


def _preflight(post_id, expected_media, *, session):
    wp = _site_post(post_id, session)
    if (wp.get("id") != post_id or wp.get("status") != "draft"
            or wp.get("author") != 4
            or wp.get("featured_media") != expected_media):
        raise BrokerBlocked("WORDPRESS_DRAFT_IDENTITY_OR_COVER_MISMATCH")
    receipt = _owner_receipt(post_id, session)
    p = receipt.get("payload") if isinstance(receipt, dict) else None
    version = receipt.get("version_sha256") if isinstance(receipt, dict) else None
    if (receipt.get("schema") != "conexo-owner-release/1"
            or not isinstance(p, dict)
            or p.get("wordpress", {}).get("post_id") != post_id
            or p.get("owner_id") != 3
            or p.get("review_mode") != "owner"
            or not isinstance(version, str) or
            not re.fullmatch(r"[a-f0-9]{64}", version)):
        raise BrokerBlocked("OWNER_GATE_RELEASE_MISSING")
    body = wp.get("content") or {}
    original = body.get("raw") if isinstance(body, dict) else None
    if (not isinstance(original, str) or
            hashlib.sha256(original.encode("utf-8")).digest() !=
            hashlib.sha256(p.get("content", "").encode("utf-8")).digest()):
        raise BrokerBlocked("OWNER_GATE_CONTENT_DRIFT")
    # This validates all thirteen real Gate evidence fields, not ChatGPT assent.
    owner_trace(receipt)
    return receipt


def _date_gmt(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _normalize_gmt(raw):
    if not isinstance(raw, str):
        return None
    return raw[:19].replace("T", " ")


def schedule_batch(start_local, *, execute=False, now=None, session=requests,
                   check_identity_fn=check_identity,
                   get_draft=None, get_receipt=None, writer=publish_via_broker):
    """Preflight all six before the first WP future write; no automatic retry."""
    now = now or datetime.now(timezone.utc)
    start = _start_at(start_local, now)
    if check_identity_fn(os.environ) != "PASS":
        raise BrokerBlocked("MKT_SERVICE_IDENTITY_NOT_VERIFIED")
    # Inject readers for isolated tests but preserve normal WordPress REST.
    checks = []
    for index, (post_id, media_id) in enumerate(POSTS):
        if get_draft is None and get_receipt is None:
            receipt = _preflight(post_id, media_id, session=session)
        else:
            # Test injection does not weaken production: both are required.
            if get_draft is None or get_receipt is None:
                raise BrokerBlocked("PREFLIGHT_READERS_MISSING")
            draft = get_draft(post_id)
            if (draft.get("id") != post_id or draft.get("status") != "draft"
                    or draft.get("author") != 4
                    or draft.get("featured_media") != media_id):
                raise BrokerBlocked("WORDPRESS_DRAFT_IDENTITY_OR_COVER_MISMATCH")
            receipt = get_receipt(post_id)
            payload = receipt.get("payload")
            if (receipt.get("schema") != "conexo-owner-release/1"
                    or not isinstance(payload, dict)
                    or payload.get("owner_id") != 3
                    or payload.get("review_mode") != "owner"
                    or payload.get("wordpress", {}).get("post_id") != post_id):
                raise BrokerBlocked("OWNER_GATE_RELEASE_MISSING")
            owner_trace(receipt)
        due = start + timedelta(minutes=10*index)
        checks.append((post_id, receipt, _date_gmt(due)))
    if not execute:
        return {"status": "SIX_SIGNED_RELEASES_READY_TO_SCHEDULE",
                "write": False, "timezone": "America/Fortaleza",
                "plan": [{"id": p, "utc": date} for p, _, date in checks]}
    scheduled = []
    for post_id, packet, when in checks:
        p = packet["payload"]
        trace = owner_trace(packet)
        try:
            result = writer(packet, core_root=".", wp_url=SITE,
                wp_user=os.environ["WP_USER"],
                wp_password=os.environ["WP_APP_PASSWORD"],
                trace_run_id=trace["run_id"], trace_packet=trace,
                intent="schedule", publication_reference=p["approval_reference"],
                post_date_gmt=when, session=session,
                require_signed_seo=False, owner_release=True)
            if (not isinstance(result, dict) or result.get("verified") is not True
                    or result.get("intent") != "schedule"
                    or result.get("post_id") != post_id):
                raise BrokerBlocked("SCHEDULE_READBACK_NOT_VERIFIED")
            if get_draft is None:
                observed = _site_post(post_id, session)
                if (observed.get("status") != "future"
                        or _normalize_gmt(observed.get("date_gmt")) != when):
                    raise BrokerBlocked("WORDPRESS_FUTURE_READBACK_MISMATCH")
        except (BrokerBlocked, KeyError, TypeError, ValueError):
            return {"status": "PARTIAL_SCHEDULE_RECONCILE_MANUALLY",
                    "scheduled_ids": scheduled, "failed_post_id": post_id,
                    "write": "UNKNOWN", "retry_automatic": False}
        scheduled.append(post_id)
    return {"status": "SIX_WORDPRESS_NATIVE_POSTS_SCHEDULED",
            "scheduled_ids": scheduled, "write": True,
            "timezone": "America/Fortaleza", "retry_automatic": False,
            "seo": "GATE_REVIEWED_NOT_NATIVE_SEO_FINALIZED"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-local", required=True, help="YYYY-MM-DDTHH:MM BRT")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = schedule_batch(args.start_local, execute=args.execute)
    except (BrokerBlocked, KeyError, TypeError, ValueError):
        result = {"status": "NO_WRITE_UNVERIFIED_GATE_OR_DATE",
                  "write": False, "retry_automatic": False}
    text = json.dumps(result, ensure_ascii=False, sort_keys=True)
    print(text)
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("Agendamento nativo ConexoTech WordPress\n\n" + text + "\n")
    return 0 if result["status"] in (
        "SIX_SIGNED_RELEASES_READY_TO_SCHEDULE",
        "SIX_WORDPRESS_NATIVE_POSTS_SCHEDULED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
