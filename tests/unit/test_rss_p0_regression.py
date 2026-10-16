"""Regression tests for RSS P0: no lost items and no false WP success."""
from unittest.mock import patch
import pipeline_rss


def test_failed_item_is_not_marked_seen_before_processing(monkeypatch):
    item = {"titulo": "Noticia tech", "link": "https://example.com/a", "fonte": "teste"}
    from mkt_flow_p0 import rss_ingestor
    monkeypatch.setattr(rss_ingestor, "FEEDS_PADRAO", {"teste": "https://example.com/feed"})
    monkeypatch.setattr("sys.argv", ["pipeline_rss.py", "--limit", "1"])
    with patch.object(rss_ingestor, "buscar_novidades", return_value={"novos": [item]}) as buscar, \
         patch.object(pipeline_rss, "processar_item", return_value={"acao": "falha", "motivo": "WP offline"}), \
         patch.object(rss_ingestor, "marcar_visto") as marcar:
        pipeline_rss.main()
        marcar.assert_not_called()
        assert buscar.call_args.kwargs["marcar"] is False


def test_success_marks_seen_after_processing(monkeypatch):
    item = {"titulo": "Noticia tech", "link": "https://example.com/a", "fonte": "teste"}
    from mkt_flow_p0 import rss_ingestor
    monkeypatch.setattr(rss_ingestor, "FEEDS_PADRAO", {"teste": "https://example.com/feed"})
    monkeypatch.setattr("sys.argv", ["pipeline_rss.py", "--limit", "1"])
    with patch.object(rss_ingestor, "buscar_novidades", return_value={"novos": [item]}), \
         patch.object(pipeline_rss, "processar_item", return_value={"acao": "publicado_rascunho"}), \
         patch.object(pipeline_rss, "publicar_indice", return_value={}), \
         patch.object(rss_ingestor, "marcar_visto") as marcar:
        pipeline_rss.main()
        marcar.assert_called_once_with("teste", item["link"], item["titulo"])


def test_wp_error_must_not_count_as_success():
    # Contract test: an explicit WordPress error must yield 'falha'.
    wp_result = {"erro": "WP 500: unavailable"}
    assert pipeline_rss.classificar_resultado_wp(wp_result) == "falha"


def test_wp_draft_confirmation_counts_as_success():
    wp_result = {"post_id": 123, "status": "draft", "link": "https://example.com/?p=123"}
    assert pipeline_rss.classificar_resultado_wp(wp_result) == "publicado_rascunho"


def test_missing_wp_configuration_is_not_success():
    assert pipeline_rss.classificar_resultado_wp({"aviso": "WP ausente"}) == "falha"
