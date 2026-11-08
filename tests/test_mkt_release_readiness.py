import json
from unittest.mock import MagicMock
from tools.mkt_release_readiness import probe, HOST, PROOF_RUN

ENV = {"WP_URL": "https://conexotech.com.br", "WP_USER": "test", "WP_APP_PASSWORD": "private-test",
       "TURSO_DATABASE_URL": "libsql://" + HOST, "CONEXO_TRACE_TURSO_ALLOWED_HOST": HOST,
       "TURSO_AUTH_TOKEN": "private-token"}


def response(code, body):
    obj = MagicMock(status_code=code, content=b"small")
    obj.json.return_value = body
    return obj


def client():
    obj = MagicMock()
    obj.request.side_effect = [
        response(422, {"code": "conexo_editorial_blocked", "message": "Contrato de publicacao invalido."}),
        response(200, {"snapshot": {"ID": 9768, "post_author": 3, "post_status": "draft", "post_content": "PRIVATE_BODY"}, "snapshot_sha256": "a" * 64}),
        response(200, {"schema": "conexo-seo-readiness/1", "editorial_gate_ready": True,
                       "seo_signing_ready": False, "seo_public_output_ready": False, "seo_key_proof": "PRIVATE_PROOF"}),
    ]
    return obj


def trace(_):
    return {"ok": True, "trace": {"run_id": PROOF_RUN, "publication_authorized": False}}


def test_probe_checks_one_invalid_contract_and_only_gets_other_wp_data():
    http = client()
    out = probe(ENV, session=http, identity_check=lambda _: "PASS", trace_read=trace)
    assert out["broker_allowlist"] == "PASS"
    assert out["turso_homolog_read"] == "PASS"
    assert out["candidate_author_id"] == 3
    assert out["seo_signing_ready"] is False
    assert out["signed_seo_broker_supported"] is False
    assert out["publication_authorized"] is False
    calls = http.request.call_args_list
    assert [c.args[0] for c in calls] == ["POST", "GET", "GET"]
    assert calls[0].kwargs["json"] == {"executor": "mkt_rss", "post_id": 0}
    for call in calls:
        assert call.kwargs["allow_redirects"] is False
    assert "PRIVATE" not in json.dumps(out)
    assert "private-test" not in json.dumps(out)
    assert "private-token" not in json.dumps(out)


def test_identity_failure_prevents_all_other_calls():
    http = client()
    read = MagicMock()
    out = probe(ENV, session=http, identity_check=lambda _: "WP_IDENTITY_MISMATCH", trace_read=read)
    assert out["identity"] == "WP_IDENTITY_MISMATCH"
    http.request.assert_not_called()
    read.assert_not_called()


def test_broker_403_is_not_allowlist_pass():
    http = client()
    http.request.side_effect = [response(403, {}), response(404, {}), response(404, {})]
    out = probe(ENV, session=http, identity_check=lambda _: "PASS", trace_read=trace)
    assert out["broker_allowlist"] == "BLOCKED"
    assert out["candidate_snapshot"] == "BLOCKED"
    assert out["editorial_gate_ready"] is False


def test_wrong_turso_host_never_receives_token():
    read = MagicMock()
    out = probe({**ENV, "TURSO_DATABASE_URL": "libsql://wrong.example"}, session=client(), identity_check=lambda _: "PASS", trace_read=read)
    read.assert_not_called()
    assert out["turso_homolog_read"] == "NOT_CONFIGURED"


def test_missing_historical_trace_and_accidental_authorization_are_blocked():
    for result in (None, {"ok": False}, {"ok": True, "trace": {"run_id": PROOF_RUN, "publication_authorized": True}}):
        out = probe(ENV, session=client(), identity_check=lambda _: "PASS", trace_read=lambda _: result)
        assert out["turso_homolog_read"] == "BLOCKED"


def test_unexpected_success_on_invalid_contract_never_reported_as_pass():
    http = client()
    http.request.side_effect = [response(200, {}), response(200, {}), response(200, {})]
    out = probe(ENV, session=http, identity_check=lambda _: "PASS", trace_read=trace)
    assert out["broker_allowlist"] == "BLOCKED"
    assert out["candidate_snapshot"] == "BLOCKED"
    assert out["seo_readiness_read"] == "BLOCKED"
