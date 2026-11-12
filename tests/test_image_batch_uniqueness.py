"""Regression: batch planning must not reuse a cover or imply unsupported rights."""

from unittest.mock import patch

import pytest

from mkt_flow_p0.image_protocol import (
    plan_image, plan_image_batch, reserve_image_candidate
)


def test_two_matching_titles_cannot_reuse_same_licensed_photo():
    result = plan_image_batch(["Teclado do iPhone: como configurar",
                               "Teclado do iPhone: novidades"], offline=True)
    assert result["schema"] == "conexo-image-batch-plan/1"
    first, second = result["plans"]
    assert first["status"] == "CANDIDATE_LICENSE_DOCUMENTED"
    assert first["content_fit_review"] == "PENDING"
    assert second["status"] == "RESEARCH_REQUIRED_OFFLINE"
    assert second["reason"] == "BATCH_COVER_ALREADY_RESERVED"
    assert first["resource"]["id"] in second["rejected_duplicate_ids"]
    assert result["ai_called"] is False
    assert result["wordpress_written"] is False


def test_reserved_candidates_not_promoted_to_approval_or_wordpress():
    ids = set()
    plan = plan_image("Teclado do iPhone")
    assert reserve_image_candidate(plan, ids) is True
    assert plan["resource"]["id"] in ids
    assert plan["resource"]["image_url"] in ids
    assert plan_image("Teclado do iPhone",
                      used_image_identifiers=ids)["status"] == "RESEARCH_REQUIRED_OFFLINE"


def test_free_stock_search_excludes_reused_url_before_ai_fallback():
    candidate = {"url": "https://images.unsplash.com/photo-test",
                 "pagina_origem": "https://unsplash.com/photos/test",
                 "revisao_visual": "PENDENTE"}
    with patch("mkt_flow_p0.image_handler.buscar_fallback",
               return_value={"candidatos": [candidate],
                             "proxima_etapa": "REVISAO_HUMANA_DE_MIDIA"}):
        result = plan_image("Título novo", offline=False,
                            used_image_identifiers={candidate["url"]})
    assert result["status"] == "AI_GENERATION_REQUIRED"
    assert result["reason"] == "NO_DISTINCT_FREE_CANDIDATE"
    assert result["ai_called"] is False
    assert result["wordpress_written"] is False


def test_distinct_free_stock_still_requires_license_and_visual_review():
    candidate = {"url": "https://images.unsplash.com/photo-distinct",
                 "pagina_origem": "https://unsplash.com/photos/distinct",
                 "revisao_visual": "PENDENTE"}
    with patch("mkt_flow_p0.image_handler.buscar_fallback",
               return_value={"candidatos": [candidate],
                             "proxima_etapa": "REVISAO_HUMANA_DE_MIDIA"}):
        result = plan_image("Título novo", offline=False,
                            used_image_identifiers={"other-image"})
    assert result["status"] == "CANDIDATES_REQUIRE_CONTENT_FIT_REVIEW"
    assert result["wordpress_written"] is False


def test_free_stock_outage_does_not_imply_ai_is_approved():
    with patch("mkt_flow_p0.image_handler.buscar_fallback",
               return_value={"erro": "sem rede",
                             "proxima_etapa": "PESQUISA_BANCO_PENDENTE"}):
        result = plan_image("Outro tema", offline=False,
                            used_image_identifiers={"old-image"})
    assert result["status"] == "FREE_STOCK_RESEARCH_PENDING"
    assert result["ai_called"] is False


def test_bad_batch_keys_fail_closed():
    with pytest.raises(ValueError, match="IMAGE_BATCH_USED_INVALID"):
        plan_image("Teclado do iPhone", used_image_identifiers="bad-input")
    with pytest.raises(ValueError, match="IMAGE_BATCH_TITLES_INVALID"):
        plan_image_batch(["good", ""])


def test_rss_processing_blocks_repeated_featured_media_before_network():
    from pipeline_rss import processar_item
    result = processar_item({"link": "https://example.org/atom"},
                            featured_media_id=123,
                            image_batch_media_used={123})
    assert result == {"acao": "bloqueado", "motivo": "capa_repetida_no_lote",
                      "escreveu": False}
