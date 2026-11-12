"""Publish a fixed set of already owner/Gate-approved WordPress drafts safely.

No approvals are created. Every Gate owner-release must validate for the exact
current draft version *before the first write*. No automatic retry if a write
is uncertain, SEO readback fails or part of the batch has already published.
"""
import argparse
import json
import os
import re

import requests

from mkt_flow_p0.editorial_broker_transport import _get_json, BrokerBlocked
from mkt_flow_p0.editorial_transport import SITE
from tools.publish_owner_approved import release
from tools.wp_identity_preflight import check_identity

_VERSION = re.compile(r"[a-f0-9]{64}\Z")


def gate_owner_version(post_id, *, session=requests):
    """Retrieve a *server-issued* release for the current exact version."""
    auth = (os.environ["WP_USER"], os.environ["WP_APP_PASSWORD"])
    packet = _get_json(
        session,
        f"{SITE}/wp-json/conexo/v1/editorial/owner-release/{post_id}",
        auth, 15,
    )
    payload = packet.get("payload")
    version = packet.get("version_sha256")
    if (packet.get("schema") != "conexo-owner-release/1"
            or not isinstance(payload, dict)
            or payload.get("wordpress", {}).get("post_id") != post_id
            or payload.get("owner_id") != 3
            or payload.get("review_mode") != "owner"
            or not isinstance(version, str) or not _VERSION.fullmatch(version)):
        raise BrokerBlocked("OWNER_RELEASE_CURRENT_VERSION_NOT_APPROVED")
    return version


def publish_batch(post_ids, *, execute=False, lookup=None, publish=None,
                  identity=None):
    """Preflight ALL articles before making ANY broker publication request."""
    if (not isinstance(post_ids, (list, tuple))
            or not 1 <= len(post_ids) <= 10
            or any(type(post_id) is not int or post_id <= 0 for post_id in post_ids)
            or len(post_ids) != len(set(post_ids))):
        raise BrokerBlocked("BATCH_POST_IDS_INVALID")
    if (identity or check_identity)(os.environ) != "PASS":
        raise BrokerBlocked("MKT_SERVICE_IDENTITY_NOT_VERIFIED")
    lookup = lookup or gate_owner_version
    publish = publish or release
    versions = {}
    checked = []
    # All signed Gate records must exist and match before the first write.
    for post_id in post_ids:
        version = lookup(post_id)
        preflight = publish(post_id, version, False)
        if (not isinstance(preflight, dict)
                or preflight.get("validated") is not True
                or preflight.get("post_id") != post_id
                or preflight.get("version_sha256") != version
                or preflight.get("write") is not False):
            raise BrokerBlocked("BATCH_PREFLIGHT_NOT_APPROVED")
        versions[post_id] = version
        checked.append(post_id)
    if not execute:
        return {"status": "ALL_GATE_PREFLIGHTS_VALID", "post_ids": checked,
                "write": False, "retry_automatic": False}
    published = []
    for post_id in post_ids:
        try:
            result = publish(post_id, versions[post_id], True)
        except (BrokerBlocked, KeyError, TypeError, ValueError):
            return {"status": "PARTIAL_PUBLICATION_RECONCILE_MANUALLY",
                    "published_ids": published, "failed_post_id": post_id,
                    "write": True, "retry_automatic": False}
        if (not isinstance(result, dict) or "erro" in result
                or result.get("verified") is not True
                or result.get("post_id") != post_id
                or result.get("seo_public_verified") is not True):
            return {"status": "PARTIAL_PUBLICATION_RECONCILE_MANUALLY",
                    "published_ids": published, "failed_post_id": post_id,
                    "write": True, "retry_automatic": False}
        published.append(post_id)
    return {"status": "ALL_PUBLICATIONS_VERIFIED", "published_ids": published,
            "write": True, "retry_automatic": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--post-ids", nargs="+", type=int, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = publish_batch(args.post_ids, execute=args.execute)
    except (BrokerBlocked, KeyError, TypeError, ValueError):
        # Never echo draft content, secrets, WP responses or full exceptions.
        result = {"status": "BATCH_GATE_PREFLIGHT_BLOCKED_NO_WRITE",
                  "write": False, "retry_automatic": False}
    safe_json = json.dumps(result, ensure_ascii=False, sort_keys=True)
    print(safe_json)
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as out:
            out.write("MKT-RSS - owner-approved batch publication\n\n" + safe_json + "\n")
    return 0 if result["status"] in (
        "ALL_PUBLICATIONS_VERIFIED", "ALL_GATE_PREFLIGHTS_VALID") else 1


if __name__ == "__main__":
    raise SystemExit(main())
