"""Fail-closed SEO preflight and safe recovery; no actual HTTP or credentials."""
import os
import hashlib
import hmac
from unittest.mock import MagicMock, patch

from mkt_flow_p0 import editorial_transport as transport

KEY = "synthetic-secret-32-bytes-offline-only-1234"
NONCE = "a" * 32
VERSION = "b" * 64

class Response:
    def __init__(self, payload):
        self.status_code = 200
        self.payload = payload
    def json(self):
        return self.payload

def package(seo=None):
    if isinstance(seo, dict):
        seo = {"provider": "native",
               "canonical": transport.SITE + "/materia-revisada/", **seo}
    return {"stage": "ready", "version_sha256": VERSION, "payload": {
        "seo": seo, "slug": "materia-revisada", "wordpress": {"post_id": 9711},
    }}

def _core():
    core = MagicMock()
    validator = core.validator.return_value
    validator.HUMAN_PENDING = "human pending"
    validator.evaluate.return_value = ([], [])
    return core

def test_strict_preflight_blocks_missing_seo_before_any_network():
    with patch.dict(os.environ, {"CONEXO_REQUIRE_SIGNED_SEO": "1",
                                  "CONEXO_EDITORIAL_GATE_KEY": KEY,
                                  "CONEXO_NATIVE_SEO_SIGNING_KEY": KEY}), \
         patch.object(transport, "load_core", return_value=_core()), \
         patch.object(transport.requests, "get") as get, \
         patch.object(transport.requests, "post") as post:
        result = transport.publish_package(package(), core_root="/unused",
            wp_url=transport.SITE, wp_user="u", wp_password="p",
            actor_id=4, intent="publish")
    assert result["erro"] == "fluxo editorial bloqueado"
    get.assert_not_called()
    post.assert_not_called()

def test_strict_preflight_blocks_missing_key_before_any_network():
    with patch.dict(os.environ, {"CONEXO_REQUIRE_SIGNED_SEO": "1",
                                  "CONEXO_EDITORIAL_GATE_KEY": KEY,
                                  "CONEXO_NATIVE_SEO_SIGNING_KEY": ""}), \
         patch.object(transport, "load_core", return_value=_core()), \
         patch.object(transport.requests, "get") as get, \
         patch.object(transport.requests, "post") as post:
        result = transport.publish_package(package({"title": "SEO", "description": "Descrição"}),
            core_root="/unused", wp_url=transport.SITE,
            wp_user="u", wp_password="p", actor_id=4, intent="publish")
    assert result["erro"] == "fluxo editorial bloqueado"
    get.assert_not_called()
    post.assert_not_called()

def test_completed_publication_resume_finalizes_seo_without_republishing():
    snapshot = {"ID": 9711, "post_content": "reviewed body"}
    result = {"post_id": 9711, "status": "publish", "intent": "publish",
              "nonce": NONCE, "version_sha256": VERSION, "snapshot": snapshot}
    get_results = [Response({"schema": "conexo-seo-readiness/1",
                             "editorial_gate_ready": True, "seo_signing_ready": True,
                             "seo_key_mode": "explicit"}),
                   Response({"state": "COMPLETE", "result": result.copy()}),
                   Response({"snapshot": snapshot})]
    with patch.dict(os.environ, {"CONEXO_REQUIRE_SIGNED_SEO": "1",
                                  "CONEXO_EDITORIAL_GATE_KEY": KEY,
                                  "CONEXO_NATIVE_SEO_SIGNING_KEY": KEY}), \
         patch.object(transport, "load_core", return_value=_core()), \
         patch.object(transport.requests, "get", side_effect=get_results), \
         patch.object(transport.requests, "post") as post, \
         patch.object(transport, "_finalize_seo_after_publish",
                      return_value={"status": "verified"}) as finalize:
        done = transport.publish_package(package({"title": "SEO", "description": "Descrição"}),
            core_root="/unused", wp_url=transport.SITE,
            wp_user="u", wp_password="p", actor_id=4, intent="publish",
            operation_nonce=NONCE, seo_publication_signature="c" * 64)
    assert done["resumed"] is True
    assert done["seo_private_delivery"]["status"] == "verified"
    post.assert_not_called()
    assert finalize.call_args.kwargs["envelope"]["signature"] == "c" * 64

def test_resume_without_original_signature_never_republishes():
    snapshot = {"ID": 9711, "post_content": "reviewed body"}
    result = {"post_id": 9711, "status": "publish", "intent": "publish",
              "nonce": NONCE, "version_sha256": VERSION, "snapshot": snapshot}
    get_results = [Response({"state": "COMPLETE", "result": result.copy()}),
                   Response({"snapshot": snapshot})]
    with patch.dict(os.environ, {"CONEXO_REQUIRE_SIGNED_SEO": "0",
                                  "CONEXO_EDITORIAL_GATE_KEY": KEY}), \
         patch.object(transport, "load_core", return_value=_core()), \
         patch.object(transport.requests, "get", side_effect=get_results), \
         patch.object(transport.requests, "post") as post:
        done = transport.publish_package(package(),
            core_root="/unused", wp_url=transport.SITE,
            wp_user="u", wp_password="p", actor_id=4, intent="publish",
            operation_nonce=NONCE)
    assert done["seo_private_delivery"]["status"] == "pending_original_publication_signature"
    assert done["seo_private_delivery"]["retry_automatic"] is False
    post.assert_not_called()


def test_strict_publish_blocks_when_server_gate_lacks_signing_key():
    with patch.dict(os.environ, {"CONEXO_REQUIRE_SIGNED_SEO": "1",
                                  "CONEXO_EDITORIAL_GATE_KEY": KEY,
                                  "CONEXO_NATIVE_SEO_SIGNING_KEY": KEY}), \
         patch.object(transport, "load_core", return_value=_core()), \
         patch.object(transport.requests, "get", return_value=Response({
             "schema": "conexo-seo-readiness/1", "editorial_gate_ready": True,
             "seo_signing_ready": False})) as get, \
         patch.object(transport.requests, "post") as post:
        result = transport.publish_package(
            package({"title": "SEO", "description": "Descrição"}),
            core_root="/unused", wp_url=transport.SITE,
            wp_user="u", wp_password="p", actor_id=4, intent="publish")
    assert result["erro"] == "fluxo editorial bloqueado"
    assert get.call_count == 1
    post.assert_not_called()

def test_single_master_key_mode_derives_separate_seo_key():
    with patch.dict(os.environ, {"CONEXO_EDITORIAL_GATE_KEY": KEY,
                                  "CONEXO_NATIVE_SEO_SIGNING_KEY": "",
                                  "CONEXO_DERIVE_SEO_KEY_FROM_EDITORIAL": "1"}):
        derived = transport._effective_seo_key()
    expected = hmac.new(KEY.encode(), b"conexo-native-seo-v1",
                        hashlib.sha256).digest()
    assert derived == expected and len(derived) == 32


def test_dedicated_seo_key_wins_and_malformed_explicit_key_fails_closed():
    with patch.dict(os.environ, {"CONEXO_EDITORIAL_GATE_KEY": KEY,
                                  "CONEXO_NATIVE_SEO_SIGNING_KEY": KEY,
                                  "CONEXO_DERIVE_SEO_KEY_FROM_EDITORIAL": "1"}):
        assert transport._effective_seo_key() == KEY.encode()
    with patch.dict(os.environ, {"CONEXO_EDITORIAL_GATE_KEY": KEY,
                                  "CONEXO_NATIVE_SEO_SIGNING_KEY": "short",
                                  "CONEXO_DERIVE_SEO_KEY_FROM_EDITORIAL": "1"}):
        assert transport._effective_seo_key() == b""

def test_strict_publish_rejects_provider_and_canonical_before_network():
    from copy import deepcopy
    valid = {"title": "SEO", "description": "Descrição"}
    for mutation in ({"provider": "rank_math"}, {"canonical": "https://evil.example/x/"},
                     {"canonical": "https://conexotech.com.br/other/"}):
        source = package({**valid, **mutation})
        with patch.dict(os.environ, {"CONEXO_REQUIRE_SIGNED_SEO": "1",
                                      "CONEXO_EDITORIAL_GATE_KEY": KEY,
                                      "CONEXO_NATIVE_SEO_SIGNING_KEY": KEY}), \
             patch.object(transport, "load_core", return_value=_core()), \
             patch.object(transport.requests, "get") as get, \
             patch.object(transport.requests, "post") as post:
            result = transport.publish_package(source, core_root="/unused",
                wp_url=transport.SITE, wp_user="u", wp_password="p",
                actor_id=4, intent="publish")
        assert result["erro"] == "fluxo editorial bloqueado"
        get.assert_not_called()
        post.assert_not_called()

def test_strict_publish_blocks_when_server_has_different_key_mode():
    server = {"schema": "conexo-seo-readiness/1",
              "editorial_gate_ready": True, "seo_signing_ready": True,
              "seo_key_mode": "derived"}
    with patch.dict(os.environ, {"CONEXO_REQUIRE_SIGNED_SEO": "1",
                                  "CONEXO_EDITORIAL_GATE_KEY": KEY,
                                  "CONEXO_NATIVE_SEO_SIGNING_KEY": KEY}), \
         patch.object(transport, "load_core", return_value=_core()), \
         patch.object(transport.requests, "get", return_value=Response(server)) as get, \
         patch.object(transport.requests, "post") as post:
        result = transport.publish_package(
            package({"title": "SEO", "description": "Descrição"}),
            core_root="/unused", wp_url=transport.SITE,
            wp_user="u", wp_password="p", actor_id=4, intent="publish")
    assert result["erro"] == "fluxo editorial bloqueado"
    assert get.call_count == 1
    post.assert_not_called()
