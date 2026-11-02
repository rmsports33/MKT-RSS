from editorial_wordpress_adapter import inspect_wordpress_draft

DRAFT = {"id": 42, "status": "draft", "categories": [10],
         "slug": "noticia", "featured_media": 21,
         "title": {"raw": "Noticia"}, "content": {"raw": "<p>Conteudo</p>"},
         "link": "https://conexotech.com.br/?p=42"}
REVIEW = {"veredito": "APROVADO", "revisao_substantiva": True,
          "evidencias_verificadas": True, "aprovacao_atual": True}


def test_reads_persisted_draft_but_blocks_uncertified_review():
    calls = []
    result = inspect_wordpress_draft(lambda post_id: (calls.append(post_id), DRAFT)[1],
                                      42, REVIEW)
    assert calls == [42]
    assert not result["authorized"]
    assert "trusted_factual_review_missing" in result["blockers"]


def test_bad_id_prevents_fetch():
    def forbidden(_):
        raise AssertionError("Must not fetch")
    result = inspect_wordpress_draft(forbidden, True, REVIEW)
    assert not result["authorized"]
    assert result["blockers"] == ["post_id_invalid"]


def test_failed_fetch_blocks():
    def failing(_):
        raise ConnectionError("unavailable")
    assert "wordpress_read_failed" in inspect_wordpress_draft(failing, 42, REVIEW)["blockers"]


def test_wrong_post_id_blocks():
    assert "wordpress_response_invalid" in inspect_wordpress_draft(
        lambda _: {**DRAFT, "id": 43}, 42, REVIEW)["blockers"]


def test_malformed_status_blocks():
    result = inspect_wordpress_draft(lambda _: {**DRAFT, "status": "publish"}, 42, REVIEW)
    assert not result["authorized"]
    assert "unexpected_status" in result["blockers"]
