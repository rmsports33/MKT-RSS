"""Real WordPress published links only, never fabricated internal URLs."""
from mkt_flow_p0.related_posts import (
    selecionar_relacionados, buscar_relacionados_wordpress, anexar_relacionados
)
from mkt_flow_p0.editorial_identity import criar_handoff_chatgpt, atualizar_handoff_revisao, validar_handoff_chatgpt
import pytest

ORIGIN="https://news.example.org/android-ia"
POSTS=[
    {"status":"publish","title":{"rendered":"Android Drop: recursos de IA no celular"},"link":"https://conexotech.com.br/android-drop-recursos-como-conferir/"},
    {"status":"publish","title":{"rendered":"Android e Windows: como integrar"},"link":"https://conexotech.com.br/android-windows-integrar/"},
    {"status":"publish","title":{"rendered":"Android: novidades para assistir vídeos"},"link":"https://conexotech.com.br/android-videos/" },
    {"status":"publish","title":{"rendered":"Patente Android em andamento"},"link":"https://evil.example/forge/"},
    {"status":"draft","title":{"rendered":"Android draft confidencial"},"link":"https://conexotech.com.br/rascunho/"},
    {"status":"publish","title":{"rendered":"Sem relação nenhuma"},"link":"https://conexotech.com.br/sem-relacao/"},
]


def test_select_real_published_relevant_only():
    selected=selecionar_relacionados("Android e IA",POSTS)
    assert len(selected)==3
    assert all(x["url"].startswith("https://conexotech.com.br/") for x in selected)
    assert all("rascunho" not in x["url"] and "evil" not in x["url"] for x in selected)


def test_no_match_never_fills_with_unrelated():
    selected=selecionar_relacionados("Tecnologia holográfica quântica inédita",POSTS)
    assert selected==[]


def test_api_read_error_is_not_replaced_by_fake_urls():
    class Dummy:
        status_code=403
        def json(self): return POSTS
    class Client:
        def get(self,*a,**k):return Dummy()
    assert buscar_relacionados_wordpress("Android IA","https://conexotech.com.br",
                                         request_client=Client())==[]


def test_safe_url_rejection_and_media_exclusion():
    records=[{"status":"publish","title":{"rendered":"Android IA"},"link":"https://conexotech.com.br.evil.example/a"},
             {"status":"publish","title":{"rendered":"Android IA"},"link":"http://conexotech.com.br/a"},
             {"status":"publish","title":{"rendered":"Android IA"},"link":"https://conexotech.com.br/?p=1"}]
    assert selecionar_relacionados("Android",records)==[]


def test_linking_version_is_new_and_review_remains_pending():
    text="## Android\n\n"+"Texto factual com atribuição externa e contexto brasileiro. "*55
    data={"titulo_seo":"Android e IA no Brasil","slug":"android-ia-no-brasil",
          "meta_description":"Panorama dos recursos anunciados e de suas implicações para o público brasileiro com exemplos e referências verificáveis sobre o sistema Android.",
          "texto_markdown":text}
    original=criar_handoff_chatgpt(data,url_fonte=ORIGIN,fonte_nome="Noticiário")
    related=selecionar_relacionados("Android IA",POSTS)
    marked=anexar_relacionados(original["markdown"],related)
    final=atualizar_handoff_revisao(original,marked,related_articles=related)
    assert final["version_sha256"]!=original["version_sha256"]
    assert final["metadata"]["related_articles"]==related
    assert final["review_status"]=="PENDING_HUMAN_REVIEW"
    assert final["metadata"]["review"]["approved"] is False
    assert validar_handoff_chatgpt(final)["valid"] is True


@pytest.mark.parametrize("invalid",[
    [{"url":"http://conexotech.com.br/a","title":"Android"}],
    [{"url":"https://evil.example.org/a","title":"Android"}],
    [{"url":"https://conexotech.com.br/a","title":""}],
])
def test_invalid_links_cannot_be_signed_into_new_version(invalid):
    data={"titulo_seo":"Android e IA no Brasil","slug":"android-ia-no-brasil",
          "meta_description":"Panorama dos recursos anunciados e de suas implicações para o público brasileiro com exemplos e referências verificáveis sobre o sistema Android.",
          "texto_markdown":"## Android\n\n"+("Fatos verificáveis sobre dispositivos Android. "*30)}
    original=criar_handoff_chatgpt(data,url_fonte=ORIGIN)
    with pytest.raises(ValueError):
        atualizar_handoff_revisao(original,original["markdown"],related_articles=invalid)


def test_featured_media_selection_is_part_of_handoff_version():
    article={"titulo_seo":"Android e IA no Brasil","slug":"android-ia-no-brasil",
             "meta_description":"Panorama dos recursos anunciados e das implicações para o público brasileiro com informações adicionais de fontes reconhecidas sobre Android.",
             "texto_markdown":"## Android\n\n"+("Texto original com explicações verificáveis. "*40)}
    initial=criar_handoff_chatgpt(article,url_fonte=ORIGIN)
    a=atualizar_handoff_revisao(initial,initial["markdown"],
                                featured_media_id=9714,media_rights_confirmed=True)
    b=atualizar_handoff_revisao(initial,initial["markdown"],
                                featured_media_id=9764,media_rights_confirmed=True)
    assert a["version_sha256"]!=b["version_sha256"]
    assert a["metadata"]["featured_image"]["wordpress_media_id"]==9714
    assert a["metadata"]["review"]["approved"] is False
    assert validar_handoff_chatgpt(a)["valid"]


def test_image_rights_alone_cannot_create_valid_version():
    article={"titulo_seo":"Android e IA no Brasil","slug":"android-ia-no-brasil",
             "meta_description":"Panorama dos recursos anunciados e das implicações para o público brasileiro com informações adicionais de fontes reconhecidas sobre Android.",
             "texto_markdown":"## Android\n\n"+("Texto original com explicações verificáveis. "*40)}
    initial=criar_handoff_chatgpt(article,url_fonte=ORIGIN)
    with pytest.raises(ValueError):
        atualizar_handoff_revisao(initial,initial["markdown"],featured_media_id=9714)
    with pytest.raises(ValueError):
        atualizar_handoff_revisao(initial,initial["markdown"],media_rights_confirmed=True)


def test_related_links_reject_query_fragment_and_credentials():
    for raw in ("https://conexotech.com.br/guia/?preview=true",
                "https://conexotech.com.br/guia/#secreto",
                "https://user:pass@conexotech.com.br/guia/"):
        with pytest.raises(ValueError):
            anexar_relacionados("Texto original", [{"title": "Guia", "url": raw}])


def test_related_headline_is_plain_markdown_data_not_an_embedded_link():
    s = anexar_relacionados("Artigo", [{
        "url": "https://conexotech.com.br/guia-android/",
        "title": "Guia [Android](https://evil.example) <img src=x>"
    }])
    assert "https://evil.example" not in s
    assert "<img" not in s
    assert s.count("](") == 1
