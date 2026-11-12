"""Six published-once WP-Cron schedules, guarded by original Gate approvals."""
from datetime import datetime, timezone
from unittest.mock import patch
import copy
import os

import pytest

from mkt_flow_p0.editorial_broker_transport import BrokerBlocked, publish_via_broker
from tools.schedule_owner_approved_wordpress import (
    POSTS, _start_at, _date_gmt, schedule_batch
)

OWNER_CHECKS = (
    "versao", "titulo", "categoria", "capa", "licenca_imagem", "fontes",
    "alegacoes", "links_internos", "seo", "html", "revisao_substantiva",
    "visual_390", "visual_1440"
)
NOW = datetime(2026, 11, 12, 19, 0, tzinfo=timezone.utc)
ENV = {"WP_USER": "unit-test-editor", "WP_APP_PASSWORD": "secret"}


def fake_packet(post_id):
    checks = {
        key: {"estado": "VERIFICADO", "evidencia": ["Revisão humana " + key]}
        for key in OWNER_CHECKS
    }
    return {
        "schema": "conexo-owner-release/1",
        "version_sha256": ("a" * 64),
        "payload": {
            "article_id": "wp:" + str(post_id),
            "content": "Text generated outside this test",
            "wordpress": {"post_id": post_id},
            "owner_id": 3,
            "review_mode": "owner",
            "approval_reference": "OWNER-3-" + str(post_id) + "-aabbccddee",
            "checks": checks,
            "seo": {"provider": "native", "title": "SEOTitle",
                    "description": "Test SEO", "canonical": "https://conexotech.com.br/test/"}
        }
    }


def fake_draft(post_id):
    return {"id": post_id, "status": "draft", "author": 4,
            "featured_media": dict(POSTS)[post_id]}


def test_expected_utc_and_10min_minimum_lead():
    assert _date_gmt(_start_at("2026-11-13T09:00", NOW)) == "2026-11-13 12:00:00"
    with pytest.raises(BrokerBlocked, match="INVALID_LOCAL_DATETIME"):
        _start_at("2026-11-31T10:00", NOW)
    with pytest.raises(BrokerBlocked, match="INVALID_LOCAL_DATETIME"):
        _start_at("2026-11-13 09:00", NOW)
    with pytest.raises(BrokerBlocked, match="TEN_MINUTES_AHEAD"):
        _start_at("2026-11-12T16:09", NOW)


def test_preflight_all_approved_is_zero_writes():
    seen = []
    with patch.dict(os.environ, ENV):
        result = schedule_batch("2026-11-13T09:00", now=NOW,
            get_draft=lambda id: seen.append(("post", id)) or fake_draft(id),
            get_receipt=lambda id: seen.append(("gate", id)) or fake_packet(id),
            writer=lambda *args, **kw: pytest.fail("No broker calls in preflight"),
            check_identity_fn=lambda _: "PASS")
    assert result["status"] == "SIX_SIGNED_RELEASES_READY_TO_SCHEDULE"
    assert result["write"] is False and len(result["plan"]) == 6
    assert result["plan"][0]["utc"] == "2026-11-13 12:00:00"
    assert result["plan"][-1]["utc"] == "2026-11-13 12:50:00"
    assert len(seen) == 12


def test_missing_owner_approval_blocks_entire_batch_before_writes():
    posted = []
    def broken(id):
        if id == 9814:
            raise BrokerBlocked("WP_READ_HTTP_REJECTED")
        return fake_packet(id)
    with patch.dict(os.environ, ENV), pytest.raises(BrokerBlocked):
        schedule_batch("2026-11-13T09:00", execute=True, now=NOW,
            get_draft=fake_draft, get_receipt=broken,
            writer=lambda *args, **kwargs: posted.append(True),
            check_identity_fn=lambda _: "PASS")
    assert posted == []


def test_change_in_cover_or_author_does_not_schedule_any_post():
    def broken(id):
        d = fake_draft(id)
        if id == 9815:
            d["featured_media"] = 9812
        return d
    writes = []
    with patch.dict(os.environ, ENV), pytest.raises(BrokerBlocked):
        schedule_batch("2026-11-13T09:00", execute=True, now=NOW,
            get_draft=broken, get_receipt=fake_packet,
            writer=lambda *args, **kw: writes.append(True),
            check_identity_fn=lambda _: "PASS")
    assert writes == []


def test_one_execution_schedules_all_six_with_existing_gate_only():
    calls = []
    def writer(packet, **kwargs):
        calls.append((kwargs["intent"], kwargs["post_date_gmt"],
                      kwargs["owner_release"], kwargs["require_signed_seo"]))
        return {"verified": True, "intent": "schedule",
                "post_id": packet["payload"]["wordpress"]["post_id"]}
    with patch.dict(os.environ, ENV):
        result = schedule_batch("2026-11-13T09:00", execute=True, now=NOW,
            get_draft=fake_draft, get_receipt=fake_packet, writer=writer,
            check_identity_fn=lambda _: "PASS")
    assert result["status"] == "SIX_WORDPRESS_NATIVE_POSTS_SCHEDULED"
    assert result["scheduled_ids"] == [p for p, _ in POSTS]
    assert len(calls) == 6
    assert all(a == "schedule" and owner is True and strict is False
               for a, _, owner, strict in calls)
    assert [b for _, b, _, _ in calls] == [
        "2026-11-13 12:00:00", "2026-11-13 12:10:00",
        "2026-11-13 12:20:00", "2026-11-13 12:30:00",
        "2026-11-13 12:40:00", "2026-11-13 12:50:00",
    ]


def test_uncertain_schedule_stops_without_retry_or_claiming_success():
    calls = []
    def writer(packet, **kwargs):
        id = packet["payload"]["wordpress"]["post_id"]
        calls.append(id)
        if id == 9815:
            raise BrokerBlocked("UNKNOWN_OUTCOME")
        return {"verified": True, "intent": "schedule", "post_id": id}
    with patch.dict(os.environ, ENV):
        result = schedule_batch("2026-11-13T09:00", execute=True, now=NOW,
            get_draft=fake_draft, get_receipt=fake_packet, writer=writer,
            check_identity_fn=lambda _: "PASS")
    assert result["status"] == "PARTIAL_SCHEDULE_RECONCILE_MANUALLY"
    assert result["scheduled_ids"] == [9813]
    assert result["failed_post_id"] == 9815
    assert calls == [9813, 9815]
    assert result["retry_automatic"] is False


def test_transport_rejects_owner_future_with_signed_seo_or_publish_without_seo():
    # Policy boundary: future posts use core WP scheduling and reviewed SEO,
    # not a false claim of completed Native SEO signing.
    from unittest.mock import MagicMock
    p = fake_packet(9813)
    s = MagicMock()
    s.get.return_value.status_code = 200
    s.get.return_value.json.return_value = p
    for intent, signed_seo in (("schedule", True), ("publish", False)):
        with pytest.raises(BrokerBlocked, match="OWNER_VERSION_NOT_AUTHENTICATED"):
            publish_via_broker(p, core_root=".", wp_url="https://conexotech.com.br",
                wp_user="svc", wp_password="pw", trace_run_id="test-run-9813",
                intent=intent, publication_reference=p["payload"]["approval_reference"],
                post_date_gmt="2026-11-13 12:00:00" if intent == "schedule" else None,
                require_signed_seo=signed_seo, owner_release=True, session=s)
    s.post.assert_not_called()
