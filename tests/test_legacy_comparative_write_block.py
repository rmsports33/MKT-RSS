"""Legacy comparative writes must not bypass the signed editorial Gate."""
from unittest.mock import patch

from mkt_flow_p0 import wp_publisher


def test_legacy_comparative_writer_refuses_direct_mcp_write():
    with patch("mkt_flow_p0.comparativo_contract.contrato_para_mcp",
               return_value={"content": "<p>Conteúdo válido</p>"}), \
         patch.object(wp_publisher, "executar_ferramenta_mcp") as mcp, \
         patch.object(wp_publisher.requests, "post") as post:
        result = wp_publisher.publicar_comparativo(
            {"test": True}, "https://conexotech.com.br", "u", "p")
    assert result["status"] == "blocked"
    assert result["retry_automatic"] is False
    assert "assinado" in result["erro"]
    mcp.assert_not_called()
    post.assert_not_called()
