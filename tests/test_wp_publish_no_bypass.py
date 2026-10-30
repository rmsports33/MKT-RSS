"""Regression: publishing must never bypass factual or persisted WP readiness."""
from unittest.mock import patch
from mkt_flow_p0.wp_publisher import publicar_no_wordpress


def test_publish_pass_does_not_send_http():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post, \
         patch("mkt_flow_p0.wp_publisher.requests.get") as get:
        result = publicar_no_wordpress(
            "Título", "<p>Texto</p>", "PASS", "https://conexotech.com.br",
            "user", "password", status_desejado="publish",
            categoria_ids=[10], slug="titulo", imagem_url="https://example.org/image.jpg")
        assert "bloqueada" in result["erro"]
        post.assert_not_called()
        get.assert_not_called()


def test_unknown_status_is_blocked_before_network():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        result = publicar_no_wordpress(
            "Título", "<p>Texto</p>", "PASS", "https://conexotech.com.br",
            "user", "password", status_desejado="future")
        assert "invalido" in result["erro"]
        post.assert_not_called()


def test_draft_payload_never_contains_publish():
    from unittest.mock import Mock
    response = Mock(status_code=201)
    response.json.return_value = {"id": 123, "status": "draft",
                                  "link": "https://conexotech.com.br/?p=123"}
    with patch("mkt_flow_p0.wp_publisher.requests.post", return_value=response) as post, \
         patch("mkt_flow_p0.wp_publisher.requests.get") as get:
        result = publicar_no_wordpress(
            "Título", "<p>Texto</p>", "UNKNOWN", "https://conexotech.com.br",
            "user", "password", status_desejado="draft",
            categoria_ids=[10], slug="titulo")
        assert result["status"] == "draft"
        assert post.call_count == 1
        assert post.call_args.kwargs["json"]["status"] == "draft"
        get.assert_not_called()


def test_publish_denied_even_when_factual_flags_are_true():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        result = publicar_no_wordpress(
            "Título", "<p>Texto</p>", "PASS", "https://conexotech.com.br",
            "user", "password", status_desejado="publish",
            revisao_factual={"veredito": "APROVADO", "revisao_substantiva": True,
                             "evidencias_verificadas": True, "aprovacao_atual": True})
        assert "bloqueada" in result["erro"]
        post.assert_not_called()
