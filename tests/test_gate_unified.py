"""Regressões da fonte única do Gate (mkt_flow_p0.gate_unified).

Nenhuma destas verificações autoriza publicação: o módulo apenas lê, valida
e normaliza o que o Gate do WordPress já decidiu.
"""
import hashlib
from unittest.mock import MagicMock

import pytest

from mkt_flow_p0.editorial_broker_transport import BrokerBlocked
from mkt_flow_p0.editorial_trace_gate import REQUIRED
from mkt_flow_p0.gate_unified import (CHECK_STAGES, GATE_CHECKS, GateBlocked,
                                       STAGE_CHECKS, build_release_trace,
                                       content_digest, content_drift,
                                       advisory_gate_receipt, batch_review_url,
                                       DECISION_D1_SCREEN, DECISION_D1_VERSION,
                                       DECISION_D1_DATE, pending_approvals,
                                       readiness_catalog, readiness_overview,
                                       read_owner_release, review_url,
                                       validate_checks, validate_owner_release,
                                       owner_version)
from tools.publish_owner_approved import owner_trace

VERSION = "b" * 64


def packet(post_id=9768, checks=None):
    keys = GATE_CHECKS
    return {
        "schema": "conexo-owner-release/1",
        "version_sha256": VERSION,
        "payload": {
            "article_id": "wp:" + str(post_id),
            "content": "<p>Private unpublished draft</p>",
            "title": "Private title",
            "slug": "private-title",
            "wordpress": {"post_id": post_id},
            "owner_id": 3,
            "review_mode": "owner",
            "approval_reference": "OWNER-3-%d-SYNTHETIC" % post_id,
            "checks": checks or {
                key: {"estado": "VERIFICADO",
                      "evidencia": ["Synthetic human review " + key]}
                for key in keys
            },
            "seo": {"provider": "native",
                    "canonical": "https://conexotech.com.br/private-title/",
                    "title": "Reviewed SEO", "description": "Reviewed description."},
        },
    }


class Response:
    status_code = 200

    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


def http(payload):
    session = MagicMock()
    session.get.return_value = Response(payload)
    return session


# --- mapa canonico de checks -------------------------------------------------

def test_every_gate_check_supports_at_least_one_stage():
    unmapped = [name for name in GATE_CHECKS if name not in CHECK_STAGES]
    assert unmapped == []


def test_every_stage_has_a_check_or_is_the_documented_import_stage():
    for stage in REQUIRED:
        if stage == "generation":
            continue
        assert STAGE_CHECKS[stage], stage


def test_previously_unmapped_checks_are_now_blocking():
    # titulo, categoria and html were verifiable in the Gate form but did not
    # support any stage, so they could be marked without blocking anything.
    assert "titulo" in STAGE_CHECKS["editorial_approval"]
    assert "categoria" in STAGE_CHECKS["editorial_approval"]
    assert "html" in STAGE_CHECKS["render_review"]


# --- validacao do recibo do proprietario ------------------------------------

def test_thirteen_checks_are_required():
    assert len(GATE_CHECKS) == 13
    p = packet()
    for name in GATE_CHECKS:
        broken = dict(p)
        broken["payload"] = dict(p["payload"])
        broken["payload"]["checks"] = dict(p["payload"]["checks"])
        broken["payload"]["checks"][name] = {"estado": "PENDENTE", "evidencia": []}
        with pytest.raises(GateBlocked, match="OWNER_CHECK_MISSING"):
            validate_owner_release(broken)


def test_service_account_cannot_be_the_human_owner():
    p = packet()
    p["payload"]["owner_id"] = 4
    with pytest.raises(GateBlocked, match="OWNER_PACKET_INVALID"):
        validate_owner_release(p)


def test_check_without_real_evidence_is_not_verified():
    p = packet()
    p["payload"]["checks"]["seo"]["evidencia"] = ["ok"]
    with pytest.raises(GateBlocked, match="OWNER_CHECK_MISSING"):
        validate_owner_release(p)


def test_owner_version_comes_from_the_server_not_from_a_pasted_hash():
    info = read_owner_release(9768, session=http(packet()), auth=("u", "p"))
    assert info["version_sha256"] == VERSION
    assert info["post_id"] == 9768
    assert info["review_url"] == review_url(9768)
    assert owner_version(9768, session=http(packet()), auth=("u", "p")) == VERSION


def test_read_owner_release_blocks_on_http_rejection():
    session = MagicMock()
    session.get.return_value = MagicMock(status_code=403)
    with pytest.raises(GateBlocked, match="WP_READ_HTTP_REJECTED"):
        read_owner_release(9768, session=session, auth=("u", "p"))


def test_read_owner_release_blocks_when_credentials_are_absent(monkeypatch):
    monkeypatch.delenv("WP_USER", raising=False)
    monkeypatch.delenv("WP_APP_PASSWORD", raising=False)
    with pytest.raises(GateBlocked, match="WP_SERVICE_ACCOUNT_NOT_CONFIGURED"):
        read_owner_release(9768, session=http(packet()))


def test_release_for_another_post_is_refused():
    with pytest.raises(GateBlocked, match="OWNER_RELEASE_POST_MISMATCH"):
        validate_owner_release(packet(9768), post_id=9810)


# --- trilha do executor ------------------------------------------------------

def test_trace_never_claims_publication_authorization():
    trace = build_release_trace(packet())
    assert trace["publication_authorized"] is False
    assert {event["stage"] for event in trace["events"]} == set(REQUIRED)


def test_tool_owner_trace_delegates_to_the_single_source():
    assert owner_trace(packet())["events"] == build_release_trace(packet())["events"]


def test_tool_owner_trace_keeps_the_stable_block_code():
    p = packet()
    p["payload"]["checks"]["fontes"]["estado"] = "PENDENTE"
    with pytest.raises(BrokerBlocked, match="OWNER_CHECK_MISSING"):
        owner_trace(p)


# --- pendencias --------------------------------------------------------------

def test_pending_index_never_invents_an_approval():
    rows = pending_approvals([{"post_id": 9768, "titulo": "Rascunho"}])
    assert rows[0]["gate"] == "aguardando_aceite"
    assert rows[0]["version_sha256"] is None
    assert rows[0]["review_url"].endswith("post_id=9768")


def test_pending_index_marks_valid_and_drifted_receipts():
    p = packet()
    approved = pending_approvals([{"post_id": 9768}], receipts={9768: p})
    assert approved[0]["gate"] == "aceito"
    drifted = pending_approvals(
        [{"post_id": 9768, "content_sha256": "c" * 64}], receipts={9768: p})
    assert drifted[0]["gate"] == "obsoleto"


def test_pending_index_marks_invalid_receipts_without_approving():
    p = packet()
    p["payload"]["owner_id"] = 4
    rows = pending_approvals([{"post_id": 9768}], receipts={9768: p})
    assert rows[0]["gate"] == "aceite_invalido"


# --- drift e prontidao -------------------------------------------------------

def test_content_drift_detects_edited_content():
    info = validate_owner_release(packet())
    assert content_drift(info, "<p>Private unpublished draft</p>") is False
    assert content_drift(info, "<p>Texto editado depois do aceite</p>") is True
    assert content_drift(info, None) is True


def test_readiness_catalog_names_every_variant_once():
    catalog = readiness_catalog()
    ids = [variant["id"] for variant in catalog]
    assert ids == ["conteudo", "wordpress", "recibos", "ambiente"]


def test_readiness_overview_never_authorizes_publication():
    overview = readiness_overview(conteudo={"status": "PRONTO"})
    assert overview["publication_authorized"] is False
    assert overview["conteudo"] == {"status": "PRONTO"}


def test_digest_of_approved_content_is_stable():
    info = validate_owner_release(packet())
    expected = hashlib.sha256(
        "<p>Private unpublished draft</p>".encode("utf-8")).hexdigest()
    assert info["content_sha256"] == expected


# --- Incremento 1: D1, D6 e D16 ---------------------------------------------

def test_decision_d1_screen_is_the_batch_review():
    assert DECISION_D1_SCREEN == "conexo-gate-revisar-lote"
    assert DECISION_D1_VERSION == "1.0"
    assert DECISION_D1_DATE == "2026-11-16"


def test_batch_review_url_is_the_canonical_screen():
    url = batch_review_url()
    assert "conexo-gate-revisar-lote" in url
    assert "owner-review" not in url
    # O link individual permanece como fallback, nao como via canonica.
    assert "conexo-owner-review" in review_url(9768)


def test_content_digest_matches_content_sha256():
    info = validate_owner_release(packet())
    assert content_digest("<p>Private unpublished draft</p>") == info["content_sha256"]
    with pytest.raises(GateBlocked):
        content_digest(None)


def test_advisory_gate_receipt_binds_to_markdown():
    info = validate_owner_release(packet())
    receipt = advisory_gate_receipt(info, markdown="<p>Private unpublished draft</p>")
    assert receipt["status"] == "approved"
    assert receipt["content_sha256"] == info["content_sha256"]
    assert receipt["reviewer"] == "wordpress-gate-owner-3"
    assert receipt["evidence"].startswith("owner-release:")
