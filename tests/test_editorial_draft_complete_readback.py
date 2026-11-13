from editorial_wordpress_readiness import validate_complete_editorial_draft, require_complete_editorial_draft
import pytest

BASE = {
    "id": 9635, "status": "draft", "categories": [10],
    "slug": "spacesail-brasil", "featured_media": 9864,
    "title": "SpaceSail homologa terminal de internet por satélite no Brasil",
    "content": "<p>" + ("Contexto editorial completo e apurado. " * 40) +
               ' <a href="https://www.gov.br/anatel/pt-br">Fonte</a> ' +
               '<a href="https://conexotech.com.br/tecnologia/">Relacionada</a></p>',
    "excerpt": "A SpaceSail homologou um terminal de internet via satélite na Anatel, mas ainda não anunciou seus planos.",
    "image_caption": "Ilustração editorial gerada por inteligência artificial, não é fotografia oficial.",
    "link": "https://conexotech.com.br/?p=9635",
}

def test_complete_draft_ready():
    assert validate_complete_editorial_draft(BASE).ready
    require_complete_editorial_draft(BASE)

@pytest.mark.parametrize("change,code", [
    ({"featured_media": 0}, "featured_image_missing"),
    ({"image_caption": ""}, "image_credit_missing"),
    ({"excerpt": ""}, "seo_excerpt_missing_or_short"),
    ({"categories": []}, "news_category_missing"),
    ({"content": "<p>Resumo curto</p>"}, "article_incomplete"),
    ({"title": "Curto"}, "title_incomplete"),
    ({"status": "publish"}, "unexpected_status"),
    ({"id": None}, "post_id_missing"),
])
def test_incomplete_draft_blocked(change, code):
    data = {**BASE, **change}
    result = validate_complete_editorial_draft(data)
    assert not result.ready
    assert code in result.errors
    with pytest.raises(ValueError, match="editorial_draft_incomplete"):
        require_complete_editorial_draft(data)

def test_external_sources_missing():
    data = {**BASE, "content": "<p>" + ("Contexto editorial completo. " * 50) +
            '<a href="https://conexotech.com.br/tecnologia/">Interna</a></p>'}
    assert "external_sources_missing" in validate_complete_editorial_draft(data).errors

def test_internal_link_missing_requires_owner_exception():
    data = {**BASE, "content": BASE["content"].replace(
        '<a href="https://conexotech.com.br/tecnologia/">Relacionada</a>', "")}
    assert "internal_link_or_owner_exception_required" in validate_complete_editorial_draft(data).errors
    assert validate_complete_editorial_draft({**data, "internal_link_exception": True}).ready

def test_missing_document_fails_closed():
    assert not validate_complete_editorial_draft(None).ready
