"""Offline regression for all-or-nothing *preflight* and no-retry release."""

import pytest

from mkt_flow_p0.editorial_broker_transport import BrokerBlocked
from tools.publish_owner_approved_batch import publish_batch

VERSION = "a" * 64


def _accepted(post_id, version, execute):
    if execute:
        return {"verified": True, "post_id": post_id,
                "seo_public_verified": True}
    return {"validated": True, "post_id": post_id,
            "version_sha256": version, "write": False}


def test_complete_preflight_never_writes():
    seen = []
    def checked(post_id, version, execute):
        seen.append((post_id, execute))
        return _accepted(post_id, version, execute)
    result = publish_batch([9810, 9813], lookup=lambda _: VERSION,
                           publish=checked, identity=lambda _: "PASS")
    assert result["status"] == "ALL_GATE_PREFLIGHTS_VALID"
    assert seen == [(9810, False), (9813, False)]


def test_missing_one_review_prevents_all_publications():
    seen = []
    def lookup(post_id):
        if post_id == 9813:
            raise BrokerBlocked("PENDING_REVIEW")
        return VERSION
    def checked(post_id, version, execute):
        seen.append((post_id, execute))
        return _accepted(post_id, version, execute)
    with pytest.raises(BrokerBlocked):
        publish_batch([9810, 9813], execute=True,
                      lookup=lookup, publish=checked, identity=lambda _: "PASS")
    assert seen == [(9810, False)]


def test_all_approved_are_published_only_after_all_preflights():
    seen = []
    def checked(post_id, version, execute):
        seen.append((post_id, execute))
        return _accepted(post_id, version, execute)
    result = publish_batch([9810, 9813], execute=True,
                           lookup=lambda _: VERSION,
                           publish=checked, identity=lambda _: "PASS")
    assert result["status"] == "ALL_PUBLICATIONS_VERIFIED"
    assert result["published_ids"] == [9810, 9813]
    assert seen == [(9810, False), (9813, False),
                    (9810, True), (9813, True)]


def test_partial_publication_stops_and_never_retries():
    seen = []
    def checked(post_id, version, execute):
        seen.append((post_id, execute))
        if post_id == 9813 and execute:
            raise BrokerBlocked("BROKER_OUTCOME_UNKNOWN_RECONCILE_NO_RETRY")
        return _accepted(post_id, version, execute)
    result = publish_batch([9810, 9813, 9814], execute=True,
                           lookup=lambda _: VERSION,
                           publish=checked, identity=lambda _: "PASS")
    assert result["status"] == "PARTIAL_PUBLICATION_RECONCILE_MANUALLY"
    assert result["published_ids"] == [9810]
    assert result["failed_post_id"] == 9813
    assert result["retry_automatic"] is False
    assert (9814, True) not in seen


def test_failed_seo_readback_does_not_retry_or_claim_publication():
    def checked(post_id, version, execute):
        if execute:
            return {"verified": True, "post_id": post_id,
                    "seo_public_verified": False,
                    "erro": "PUBLICATION_CONFIRMED_SEO_PENDING"}
        return _accepted(post_id, version, execute)
    result = publish_batch([9810], execute=True, lookup=lambda _: VERSION,
                           publish=checked, identity=lambda _: "PASS")
    assert result["status"] == "PARTIAL_PUBLICATION_RECONCILE_MANUALLY"
    assert result["published_ids"] == []


def test_duplicate_ids_or_wrong_identity_fail_before_reading_gate():
    for ids in ([9810, 9810], [], [0], ["9810"]):
        with pytest.raises(BrokerBlocked):
            publish_batch(ids, lookup=lambda _: VERSION,
                          identity=lambda _: "PASS")
    with pytest.raises(BrokerBlocked, match="IDENTITY_NOT_VERIFIED"):
        publish_batch([9810], lookup=lambda _: VERSION,
                      identity=lambda _: "FAIL")
