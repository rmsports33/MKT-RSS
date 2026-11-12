"""Single, date-bound, Gate-approved publication slot for ConexoTech (12 Nov 2026).

All timestamps are UTC; 19:00 UTC == 16:00 America/Fortaleza (UTC-03).
GitHub Actions cron dispatch can be delayed. A slot never publishes early,
never catches up into another slot and never retries an uncertain write.
The only authorizer is an authenticated, current WordPress Gate owner-release.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import requests

from mkt_flow_p0.editorial_broker_transport import BrokerBlocked, _get_json
from mkt_flow_p0.editorial_transport import SITE
from tools.publish_owner_approved import release
from tools.publish_owner_approved_batch import gate_owner_version
from tools.wp_identity_preflight import check_identity

SLOTS = (
    ("0 19 12 11 *", 9813, 9839),
    ("10 19 12 11 *", 9815, 9841),
    ("20 19 12 11 *", 9814, 9840),
    ("30 19 12 11 *", 9810, 9838),
    ("40 19 12 11 *", 9816, 9842),
    ("50 19 12 11 *", 9817, 9843),
)
DAY = "2026-11-12"
START_HOUR_UTC = 19


def _blocked(reason, *, post_id=None):
    return {"status": reason, "post_id": post_id, "write": False,
            "retry_automatic": False}


def _read_post(post_id, *, http=requests):
    """Read status and author using the existing authenticated WordPress service."""
    auth = (os.environ["WP_USER"], os.environ["WP_APP_PASSWORD"])
    return _get_json(http,
                     f"{SITE}/wp-json/wp/v2/posts/{post_id}?context=edit",
                     auth, 15)


def run_slot(cron, *, now=None, read_post=None, lookup=None, publisher=None,
             identity=None):
    """Run only this cron slot; validated Gate receipt is required for writing."""
    if cron not in {slot[0] for slot in SLOTS}:
        return _blocked("UNKNOWN_SLOT")
    i = next(i for i, slot in enumerate(SLOTS) if slot[0] == cron)
    _, post_id, media_id = SLOTS[i]
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        return _blocked("CLOCK_MISSING_TZ", post_id=post_id)
    now = now.astimezone(timezone.utc)
    due = datetime(2026, 11, 12, START_HOUR_UTC, i * 10, tzinfo=timezone.utc)
    if now < due:
        return _blocked("SLOT_NOT_STARTED", post_id=post_id)
    if now >= due + timedelta(minutes=9):
        return _blocked("SLOT_TOO_LATE_NO_CATCHUP", post_id=post_id)
    if (identity or check_identity)(os.environ) != "PASS":
        return _blocked("MKT_SERVICE_IDENTITY_NOT_VERIFIED", post_id=post_id)
    read_post = read_post or _read_post
    lookup = lookup or gate_owner_version
    publisher = publisher or release

    # Preserve the requested 10-minute spacing even when Actions starts late.
    if i:
        prev_id = SLOTS[i - 1][1]
        try:
            previous = read_post(prev_id)
        except (BrokerBlocked, KeyError, TypeError, ValueError):
            return _blocked("PREVIOUS_READBACK_UNAVAILABLE", post_id=post_id)
        if previous.get("id") != prev_id or previous.get("status") != "publish":
            return _blocked("PREVIOUS_POST_NOT_PUBLISHED", post_id=post_id)
        when = previous.get("date_gmt")
        if not isinstance(when, str) or not when:
            return _blocked("PREVIOUS_PUBLICATION_DATE_MISSING", post_id=post_id)
        try:
            at = datetime.fromisoformat(when.replace("Z", "+00:00"))
            if at.tzinfo is None:
                at = at.replace(tzinfo=timezone.utc)
        except ValueError:
            return _blocked("PREVIOUS_PUBLICATION_DATE_INVALID", post_id=post_id)
        if now - at.astimezone(timezone.utc) < timedelta(minutes=10):
            return _blocked("PREVIOUS_POST_TOO_RECENT", post_id=post_id)
    try:
        current = read_post(post_id)
    except (BrokerBlocked, KeyError, TypeError, ValueError):
        return _blocked("CURRENT_POST_UNAVAILABLE", post_id=post_id)
    if (current.get("id") != post_id or current.get("status") != "draft"
            or current.get("author") != 4
            or current.get("featured_media") != media_id):
        return _blocked("CURRENT_DRAFT_VERSION_OR_COVER_CHANGED", post_id=post_id)
    try:
        version = lookup(post_id)  # Gate signed current version, NOT a chat hash.
        preflight = publisher(post_id, version, False)
    except (BrokerBlocked, KeyError, TypeError, ValueError):
        return _blocked("GATE_REVIEW_NOT_AUTHENTICATED", post_id=post_id)
    if (not isinstance(preflight, dict)
            or preflight.get("validated") is not True
            or preflight.get("post_id") != post_id
            or preflight.get("version_sha256") != version
            or preflight.get("write") is not False):
        return _blocked("GATE_PREFLIGHT_FAILED", post_id=post_id)
    try:
        result = publisher(post_id, version, True)
    except (BrokerBlocked, KeyError, TypeError, ValueError):
        return {"status": "PUBLICATION_OUTCOME_UNKNOWN_INSPECT_NO_RETRY",
                "post_id": post_id, "write": "UNKNOWN",
                "retry_automatic": False}
    if (not isinstance(result, dict) or "erro" in result
            or result.get("verified") is not True
            or result.get("post_id") != post_id
            or result.get("seo_public_verified") is not True):
        return {"status": "PUBLICATION_UNCERTAIN_RECONCILE_NO_RETRY",
                "post_id": post_id, "write": "UNKNOWN",
                "retry_automatic": False}
    return {"status": "PUBLISHED_GATE_APPROVED_AND_PUBLIC_SEO_VERIFIED",
            "post_id": post_id, "write": True, "retry_automatic": False}


def main():
    cron = os.getenv("CONEXO_SCHEDULE_CRON", "")
    try:
        result = run_slot(cron)
    except (BrokerBlocked, OSError, KeyError, TypeError, ValueError):
        result = _blocked("SLOT_BLOCKED_INSPECT_NO_RETRY")
    safe = json.dumps(result, ensure_ascii=False, sort_keys=True)
    print(safe)
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as out:
            out.write("ConexoTech: janela 16h - 16h50 BRT / 12-11-2026\n\n"
                      + safe + "\n")
    return 0 if result["status"] == "PUBLISHED_GATE_APPROVED_AND_PUBLIC_SEO_VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
