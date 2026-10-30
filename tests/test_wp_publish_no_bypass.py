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
