"""Regressões do wrapper WordPress: nenhuma escrita sem pacote canônico."""
from unittest.mock import patch
from mkt_flow_p0.wp_publisher import publicar_no_wordpress


def test_bloqueia_publish_sem_pass():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        r = publicar_no_wordpress("T", "<p>x</p>", "UNKNOWN", "https://site.com",
                                  "u", "p", status_desejado="publish")
        assert "erro" in r
        post.assert_not_called()


def test_draft_sem_pacote_revisado_nao_escreve():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        r = publicar_no_wordpress("T", "<p>x</p>", "UNKNOWN", "https://site.com", "u", "p")
        assert "erro" in r
        post.assert_not_called()


def test_pass_sozinho_nao_publica():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        r = publicar_no_wordpress("T", "<p>x</p>", "PASS", "https://site.com",
                                  "u", "p", status_desejado="publish")
        assert "erro" in r
        post.assert_not_called()


def test_sem_credencial_erro():
    assert "erro" in publicar_no_wordpress("T", "<p>x</p>", "PASS", "", "", "")
