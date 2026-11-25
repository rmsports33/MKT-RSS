"""Mandatory editorial_assessment in publish_package. No real network.

Covers: missing, invalid, pending assessment; wp_broker bypass closed;
stage/draft remain compatible.
"""
import os
import pytest
from unittest.mock import patch

from mkt_flow_p0 import editorial_transport as t
from mkt_flow_p0.wp_destination import CANONICAL_SITE

ENV = {
    "WP_OPERATION_MODE": "production",
    "GITHUB_ENVIRONMENT": "",
    "WP_URL": CANONICAL_SITE,
    "WP_USER": "svc",
    "WP_APP_PASSWORD": "synthetic",
}


def package(assessment=None):
    p = {
        "version_sha256": "a" * 64,
        "editorial_assessment": assessment,
        "payload": {"wordpress": {"post_id": 1}, "substantive_review": {"article_format": "guia"}},
    }
    return p


def call(pkg, intent="publish", broker=False):
    env = dict(ENV)
    if broker:
        env["CONEXO_EDITORIAL_TRANSPORT"] = "wp_broker"
    else:
        env.pop("CONEXO_EDITORIAL_TRANSPORT", None)
    with patch.dict(os.environ, env, clear=False):
        return t.publish_package(
            pkg, core_root="/unused", wp_url=CANONICAL_SITE,
            wp_user="svc", wp_password="synthetic", actor_id=3,
            intent=intent,
        )


def reason(out):
    return str(out.get("reason", "")) + str(out.get("erro", ""))


def test_missing_assessment_blocks_publish():
    out = call(package(None))
    assert "erro" in out
    assert "editorial_assessment" in reason(out)


def test_missing_assessment_blocks_wp_broker_bypass():
    out = call(package(None), broker=True)
    assert "erro" in out
    assert "editorial_assessment" in reason(out)


def test_invalid_assessment_blocks_wp_broker():
    out = call(package("not-a-dict"), broker=True)
    assert "erro" in out
    assert "editorial_assessment" in reason(out)


def test_pending_assessment_blocks_publish():
    assessment = {"brief": {}, "review": {}, "receipts": []}
    with patch("mkt_flow_p0.editorial_substance.assess_editorial_package",
               return_value={"status": "PENDING", "blockers": ["fonte_sem_evidencia"]}):
        out = call(package(assessment))
    assert "erro" in out
    assert "pendente" in reason(out)


def test_stage_does_not_require_assessment():
    # Stage/draft must reach the core validator path, not fail on assessment.
    with patch("mkt_flow_p0.editorial_transport.load_core") as lc:
        core = lc.return_value
        core.validator.return_value.evaluate.return_value = ([], [])
        out = call(package(None), intent="stage")
    # It proceeds past assessment; failure (if any) comes from other checks.
    assert "editorial_assessment" not in str(out)


def test_draft_does_not_require_assessment():
    with patch("mkt_flow_p0.editorial_transport.load_core") as lc:
        core = lc.return_value
        core.validator.return_value.evaluate.return_value = ([], [])
        out = call(package(None), intent="draft")
    assert "editorial_assessment" not in str(out)
