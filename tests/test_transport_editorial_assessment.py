"""Editorial evidence supplied to signed transport must be checked before network."""
from unittest.mock import patch
from mkt_flow_p0.editorial_transport import publish_package


def test_supplied_invalid_assessment_blocks_without_network():
    package = {"editorial_assessment": {"brief": None, "review": None, "receipts": {}},
               "payload": {"content": "# Artigo\n\nConteúdo em revisão."}}
    with patch("mkt_flow_p0.editorial_transport.load_core") as core, \
         patch("mkt_flow_p0.editorial_transport.requests.post") as post, \
         patch("mkt_flow_p0.editorial_transport.requests.get") as get:
        core.return_value.validator.return_value.evaluate.return_value = ([], [])
        result = publish_package(
            package, core_root=".", wp_url="https://conexotech.com.br",
            wp_user="u", wp_password="p", actor_id=1, intent="publish")
    assert result["erro"] == "fluxo editorial bloqueado"
    assert "avaliação substantiva pendente" in result["reason"]
    post.assert_not_called()
    get.assert_not_called()
