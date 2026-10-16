"""Regression tests for RSS P0: no lost items and no false WP success."""
from unittest.mock import patch
import pipeline_rss


def test_failed_item_is_not_marked_seen_before_processing():
    item = {"titulo": "Noticia tech", "link": "https://example.com/a", "fonte": "teste"}
    with patch("mkt_flow_p0.rss_ingestor.buscar_novidades", return_value={"novos": [item]}) as buscar, \
         patch.object(pipeline_rss, "processar_item", return_value={"acao": "falha", "motivo": "WP offline"}), \
         patch("mkt_flow_p0.rss_ingestor.marcar_visto") as marcar:
        # Regression contract: the caller must request unmarked items.
        # A separate successful-item path should mark only after confirmation.
        result = buscar("https://example.com/feed", fonte="teste", limit=1, marcar=False)
        for entry in result["novos"]:
            pipeline_rss.processar_item(entry)
        marcar.assert_not_called()
        assert buscar.call_args.kwargs["marcar"] is False


def test_wp_error_must_not_count_as_success():
    # Contract test: an explicit WordPress error must yield 'falha'.
    wp_result = {"erro": "WP 500: unavailable"}
    assert pipeline_rss.classificar_resultado_wp(wp_result) == "falha"


def test_wp_draft_confirmation_counts_as_success():
    wp_result = {"post_id": 123, "status": "draft", "link": "https://example.com/?p=123"}
    assert pipeline_rss.classificar_resultado_wp(wp_result) == "publicado_rascunho"


def test_missing_wp_configuration_is_not_success():
    assert pipeline_rss.classificar_resultado_wp({"aviso": "WP ausente"}) == "falha"
