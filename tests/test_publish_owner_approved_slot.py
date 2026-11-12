"""No-write and spacing rules for time-locked, version-signed releases."""
from datetime import datetime, timezone

from mkt_flow_p0.editorial_broker_transport import BrokerBlocked
from tools.publish_owner_approved_slot import SLOTS, run_slot

VERSION = "a" * 64


def t(minute, second=5):
    return datetime(2026, 11, 12, 19, minute, second, tzinfo=timezone.utc)


def reader(post_id):
    if post_id == 9813:
        return {"id": 9813, "status": "publish", "date_gmt": "2026-11-12T19:00:01"}
    return {"id": post_id, "status": "draft", "author": 4, "featured_media": 9841}


def publisher(post_id, version, execute):
    if not execute:
        return {"validated": True, "post_id": post_id,
                "version_sha256": version, "write": False}
    return {"verified": True, "post_id": post_id,
            "seo_public_verified": True}


def first_post(post_id):
    return {"id": post_id, "status": "draft",
            "author": 4, "featured_media": 9839}


def test_earlier_than_16h_cannot_publish():
    result = run_slot(SLOTS[0][0], now=t(0).replace(hour=18),
                      identity=lambda _: "PASS")
    assert result["status"] == "SLOT_NOT_STARTED"


def test_run_is_date_locked_and_does_not_catch_up():
    assert run_slot(SLOTS[0][0], now=t(9), identity=lambda _: "PASS")["status"] == "SLOT_TOO_LATE_NO_CATCHUP"
    assert run_slot(SLOTS[0][0], now=t(0).replace(year=2027), identity=lambda _: "PASS")["status"] == "SLOT_TOO_LATE_NO_CATCHUP"


def test_missing_gate_receipt_never_writes():
    called = []
    def missing(post_id):
        called.append(("gate", post_id))
        raise BrokerBlocked("PENDING")
    def no_write(*args):
        called.append(("write", args))
    result = run_slot(SLOTS[0][0], now=t(0),
                      read_post=first_post, lookup=missing,
                      publisher=no_write, identity=lambda _: "PASS")
    assert result["status"] == "GATE_REVIEW_NOT_AUTHENTICATED"
    assert called == [("gate", 9813)]


def test_valid_first_slot_publishes_via_real_publisher_contract():
    calls = []
    def observe(post_id, version, execute):
        calls.append((post_id, execute))
        return publisher(post_id, version, execute)
    result = run_slot(SLOTS[0][0], now=t(0), read_post=first_post,
                      lookup=lambda _: VERSION, publisher=observe,
                      identity=lambda _: "PASS")
    assert result["status"] == "PUBLISHED_GATE_APPROVED_AND_PUBLIC_SEO_VERIFIED"
    assert calls == [(9813, False), (9813, True)]


def test_previous_publication_requires_ten_full_minutes():
    def recent(post_id):
        if post_id == 9813:
            return {"id": 9813, "status": "publish",
                    "date_gmt": "2026-11-12T19:05:00"}
        return reader(post_id)
    result = run_slot(SLOTS[1][0], now=t(10), read_post=recent,
                      lookup=lambda _: VERSION, publisher=publisher,
                      identity=lambda _: "PASS")
    assert result["status"] == "PREVIOUS_POST_TOO_RECENT"


def test_second_slot_after_ten_minutes_may_publish():
    result = run_slot(SLOTS[1][0], now=t(10), read_post=reader,
                      lookup=lambda _: VERSION, publisher=publisher,
                      identity=lambda _: "PASS")
    assert result["post_id"] == 9815
    assert result["status"] == "PUBLISHED_GATE_APPROVED_AND_PUBLIC_SEO_VERIFIED"


def test_wrong_author_or_featured_image_fails_before_gate():
    def wrong(post_id):
        return {"id": post_id, "status": "draft", "author": 3,
                "featured_media": 9839}
    result = run_slot(SLOTS[0][0], now=t(0), read_post=wrong,
                      lookup=lambda _: VERSION, publisher=publisher,
                      identity=lambda _: "PASS")
    assert result["status"] == "CURRENT_DRAFT_VERSION_OR_COVER_CHANGED"


def test_uncertain_write_does_not_claim_success_or_retry():
    def uncertain(post_id, version, execute):
        if execute:
            raise BrokerBlocked("BROKER_OUTCOME_UNKNOWN")
        return publisher(post_id, version, execute)
    result = run_slot(SLOTS[0][0], now=t(0), read_post=first_post,
                      lookup=lambda _: VERSION, publisher=uncertain,
                      identity=lambda _: "PASS")
    assert result["status"] == "PUBLICATION_OUTCOME_UNKNOWN_INSPECT_NO_RETRY"
    assert result["retry_automatic"] is False
