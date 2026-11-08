from editorial_publish_transition import plan_publish_transition, verify_publish_readback

POST = {"id": 42, "status": "draft", "categories": [10],
        "slug": "exemplo", "featured_media": 12, "title": "Notícia",
        "content": "<p>Verificada</p>", "link": "https://conexotech.com.br/?p=42"}
REVIEW = {"veredito": "APROVADO", "revisao_substantiva": True,
          "evidencias_verificadas": True, "aprovacao_atual": True}


def test_self_asserted_review_cannot_authorize_publication():
    result = plan_publish_transition(POST, REVIEW)
    assert not result["allowed"]
    assert result["request"] is None
    assert "trusted_approval_and_atomic_transition_missing" in result["errors"]


def test_plan_denied_without_verified_evidence():
    result = plan_publish_transition(POST, {**REVIEW, "evidencias_verificadas": False})
    assert not result["allowed"]
    assert result["request"] is None


def test_plan_denied_without_image():
    result = plan_publish_transition({**POST, "featured_media": 0}, REVIEW)
    assert not result["allowed"]


def test_readback_requires_matching_id_and_publish_status():
    assert verify_publish_readback(42, {"id": 42, "status": "publish"})
    assert not verify_publish_readback(42, {"id": 42, "status": "draft"})
    assert not verify_publish_readback(42, {"id": 41, "status": "publish"})
