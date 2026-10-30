from editorial_publish_gate import authorize_publish, require_publish_authorization
import pytest

POST = {"id": 123, "status": "draft", "categories": [10],
        "slug": "noticia-verificada", "featured_media": 456,
        "title": "Notícia verificada", "content": "<p>Texto confirmado</p>",
        "link": "https://conexotech.com.br/?p=123"}
REVIEW = {"veredito": "APROVADO", "revisao_substantiva": True,
          "evidencias_verificadas": True, "aprovacao_atual": True}


def test_all_gates_pass():
    assert authorize_publish(POST, REVIEW) == {"autorizado": True, "bloqueios": []}
    require_publish_authorization(POST, REVIEW)


@pytest.mark.parametrize("key,value", [
    ("veredito", "SEM_ALERTAS"),
    ("revisao_substantiva", False),
    ("evidencias_verificadas", False),
    ("aprovacao_atual", False),
])
def test_factual_gate_fails_closed(key, value):
    result = authorize_publish(POST, {**REVIEW, key: value})
    assert not result["autorizado"]
    with pytest.raises(PermissionError):
        require_publish_authorization(POST, {**REVIEW, key: value})


def test_missing_factual_review():
    assert "factual_review_missing" in authorize_publish(POST, None)["bloqueios"]


def test_media_missing_even_with_approved_facts():
    result = authorize_publish({**POST, "featured_media": 0}, REVIEW)
    assert "featured_image_missing" in result["bloqueios"]


def test_published_post_is_not_valid_transition_source():
    assert not authorize_publish({**POST, "status": "publish"}, REVIEW)["autorizado"]
