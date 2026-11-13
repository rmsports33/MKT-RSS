"""Regression: retired staging must never receive WordPress draft writes.

No network, credentials, database, approval, scheduling or publication.
"""
from unittest.mock import Mock

from mkt_flow_p0.wp_draft_staging import stage_rss_draft

def test_retired_staging_is_rejected_before_network():
    client = Mock()
    result = stage_rss_draft(
        title="Uma pauta de tecnologia para o ConexoTech",
        content="<p>" + "Texto de rascunho editorial não aprovado. " * 8 + "</p>",
        source_url="https://example.org/noticia",
        wp_url="https://staging.conexotech.com.br",
        wp_user="test-user",
        wp_password="synthetic-password",
        request_client=client,
    )
    assert result["acao"] == "bloqueado"
    assert result["motivo"] == "entrada_rascunho_invalida"
    assert result["escreveu"] is False
    client.get.assert_not_called()
    client.post.assert_not_called()
