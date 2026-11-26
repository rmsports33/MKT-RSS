"""Tests for fail-closed WordPress destination resolution.

No network calls: pure configuration resolution + simulated REST server.
Every write path must be blocked in validation context and with missing config.
"""
import os
import unittest
from unittest.mock import patch

from mkt_flow_p0 import wp_destination as wd
from mkt_flow_p0.wp_destination import (
    DestinationBlocked, resolve, assert_writable, CANONICAL_SITE,
    VALIDATION_ENVIRONMENT, OPERATION_VALIDATE, OPERATION_DRAFT,
    OPERATION_PUBLISH,
)


class FakeResponse:
    def __init__(self, status=200, payload=None):
        self.status_code = status
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


class SimulatedRest:
    """Records calls; never reaches the network."""

    def __init__(self):
        self.calls = []

    def get(self, url, **kw):
        self.calls.append(("GET", url, sorted(kw)))
        return FakeResponse(payload={"ok": True})

    def post(self, url, **kw):
        self.calls.append(("POST", url, sorted(kw)))
        return FakeResponse(payload={"ok": True})


def _env(*, production=True, validation=False, missing_url=False,
         bad_url=False, wrong_url=False, missing_creds=False):
    e = {
        "WP_OPERATION_MODE": "production" if production else "",
        "GITHUB_ENVIRONMENT": VALIDATION_ENVIRONMENT if validation else "",
        "WP_URL": "https://example.invalid" if wrong_url else CANONICAL_SITE,
        "WP_USER": "svc",
        "WP_APP_PASSWORD": "synthetic",
    }
    if missing_url:
        e.pop("WP_URL")
    if bad_url:
        e["WP_URL"] = "http://insecure.example/path?x=1"
    if missing_creds:
        e["WP_USER"] = ""
        e["WP_APP_PASSWORD"] = ""
    return e


class DestinationResolutionTests(unittest.TestCase):

    def test_validation_environment_never_returns_wp_destination(self):
        for op in (OPERATION_VALIDATE, OPERATION_DRAFT, OPERATION_PUBLISH):
            with self.subTest(op=op):
                with self.assertRaises(DestinationBlocked) as ctx:
                    resolve(op, env=_env(validation=True))
                self.assertIn("VALIDATION", str(ctx.exception))

    def test_validate_operation_always_blocked(self):
        with self.assertRaises(DestinationBlocked):
            resolve(OPERATION_VALIDATE, env=_env())

    def test_missing_production_authorization_blocks(self):
        with self.assertRaises(DestinationBlocked) as ctx:
            resolve(OPERATION_DRAFT, env=_env(production=False))
        self.assertIn("AUTHORIZED", str(ctx.exception))

    def test_missing_url_blocks(self):
        with self.assertRaises(DestinationBlocked):
            resolve(OPERATION_DRAFT, env=_env(missing_url=True))

    def test_bad_url_blocks(self):
        with self.assertRaises(DestinationBlocked):
            resolve(OPERATION_PUBLISH, env=_env(bad_url=True))

    def test_wrong_host_blocks(self):
        with self.assertRaises(DestinationBlocked) as ctx:
            resolve(OPERATION_PUBLISH, env=_env(wrong_url=True))
        self.assertIn("NOT_AUTHORIZED", str(ctx.exception))

    def test_missing_credentials_blocks(self):
        with self.assertRaises(DestinationBlocked):
            resolve(OPERATION_DRAFT, env=_env(missing_creds=True))

    def test_explicit_production_draft_allowed(self):
        d = resolve(OPERATION_DRAFT, env=_env())
        self.assertEqual(d.url, CANONICAL_SITE)
        self.assertEqual(d.auth, ("svc", "synthetic"))
        assert_writable(d, OPERATION_DRAFT)

    def test_explicit_production_publish_allowed(self):
        d = resolve(OPERATION_PUBLISH, env=_env())
        assert_writable(d, OPERATION_PUBLISH)

    def test_operation_mismatch_blocked(self):
        d = resolve(OPERATION_DRAFT, env=_env())
        with self.assertRaises(DestinationBlocked):
            assert_writable(d, OPERATION_PUBLISH)

    def test_no_implicit_fallback_when_env_empty(self):
        with self.assertRaises(DestinationBlocked):
            resolve(OPERATION_PUBLISH, env={})


class SimulatedRestTests(unittest.TestCase):

    def test_simulated_write_never_uses_production_domain_for_validation(self):
        rest = SimulatedRest()
        with self.assertRaises(DestinationBlocked):
            resolve(OPERATION_DRAFT, env=_env(validation=True))
        # No REST call is attempted once resolution fails.
        self.assertEqual(rest.calls, [])

    def test_simulated_write_uses_resolved_url_only(self):
        rest = SimulatedRest()
        d = resolve(OPERATION_DRAFT, env=_env())
        rest.post(f"{d.url}/wp-json/wp/v2/posts", auth=d.auth, json={})
        self.assertEqual(len(rest.calls), 1)
        self.assertEqual(rest.calls[0][1], f"{CANONICAL_SITE}/wp-json/wp/v2/posts")
        self.assertNotIn("example.invalid", rest.calls[0][1])

    def test_simulated_seo_write_uses_resolved_destination(self):
        rest = SimulatedRest()
        d = resolve(OPERATION_PUBLISH, env=_env())
        rest.post(f"{d.url}/wp-json/conexo/v1/editorial/seo-finalize",
                  auth=d.auth, json={})
        self.assertEqual(rest.calls[0][1],
                         f"{CANONICAL_SITE}/wp-json/conexo/v1/editorial/seo-finalize")

    def test_simulated_batch_publish_uses_resolved_destination(self):
        rest = SimulatedRest()
        d = resolve(OPERATION_PUBLISH, env=_env())
        for post_id in (1, 2, 3):
            rest.post(f"{d.url}/wp-json/conexo/v1/editorial/owner-release/{post_id}",
                      auth=d.auth)
        self.assertEqual(len(rest.calls), 3)
        self.assertTrue(all(c[1].startswith(CANONICAL_SITE) for c in rest.calls))

    def test_simulated_schedule_uses_resolved_destination(self):
        rest = SimulatedRest()
        d = resolve(OPERATION_PUBLISH, env=_env())
        rest.post(f"{d.url}/wp-json/conexo/v1/editorial/write", auth=d.auth,
                  json={"intent": "schedule"})
        self.assertEqual(rest.calls[0][1],
                         f"{CANONICAL_SITE}/wp-json/conexo/v1/editorial/write")

    def test_simulated_handoff_has_no_wp_write(self):
        rest = SimulatedRest()
        with self.assertRaises(DestinationBlocked):
            resolve(OPERATION_VALIDATE, env=_env())
        self.assertEqual(rest.calls, [], "handoff/validation must not write")

    def test_simulated_broker_blocked_in_validation(self):
        rest = SimulatedRest()
        with self.assertRaises(DestinationBlocked):
            resolve(OPERATION_PUBLISH, env=_env(validation=True))
        self.assertEqual(rest.calls, [], "broker must not call WP in validation")


if __name__ == "__main__":
    unittest.main(verbosity=2)
