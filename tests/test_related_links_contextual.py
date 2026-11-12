"""Contextual related links: published-only, relevant, safe, no repeated headings."""
from mkt_flow_p0.related_posts import (
    anexar_relacionados, buscar_relacionados_wordpress,
    inserir_links_contextuais, selecionar_relacionados,
)

POSTS = [
    {"status": "publish", "title": "Tesla Optimus: produção industrial",
     "link": "https://conexotech.com.br/optimus-producao-fremont-limites-2026/"},
    {"status": "publish", "title": "Unitree G1: configurações",
     "link": "https://conexotech.com.br/unitree-r1-g1-importacao-brasil-guia/"},
    {"status": "draft", "title": "Tesla Optimus: protótipo privado",
     "link": "https://conexotech.com.br/tesla-prototipo-privado/"},
]


def test_published_related_posts_get_inline_links_and_end_section():
    related = selecionar_relacionados("Tesla Optimus e Unitree G1", POSTS)
    assert len(related) == 2
    text = ("## Robôs humanoides\n\n"
            "O Optimus tem uma proposta de robótica industrial.\n\n"
            "O Unitree G1 exige conferir a configuração.\n")
    result = anexar_relacionados(text, related)
    assert "[Optimus](https://conexotech.com.br/optimus-producao-fremont-limites-2026/)" in result
    assert "## Leia também" in result
    assert result.count("## Leia também") == 1
    assert "tesla-prototipo-privado" not in result


def test_html_existing_markdown_link_and_code_not_rewritten():
    related = selecionar_relacionados("Tesla Optimus", POSTS)
    url = related[0]["url"]
    text = (
        "## Optimus\n\n"
        "[Optimus](https://tesla.com/ai) informou algo.\n\n"
        "Veja " + chr(96) + "Optimus" + chr(96) + " no exemplo.\n\n"
        "O Optimus aparece em um texto simples.\n"
    )
    result = anexar_relacionados(text, related)
    assert "## Optimus" in result
    assert "[Optimus](https://tesla.com/ai)" in result
    assert "[Optimus](" + url + ")" in result
    assert "Veja " + chr(96) + "Optimus" + chr(96) in result


def test_generic_title_overlap_does_not_recommend_unrelated_articles():
    unrelated = [{"status": "publish", "title": "Notícia de tecnologia no Brasil 2026",
                  "link": "https://conexotech.com.br/tecnologia-generica/"}]
    assert selecionar_relacionados("Outra notícia de tecnologia no Brasil 2026", unrelated) == []


def test_unavailable_site_stays_fail_closed():
    class Bad:
        status_code = 429
    class Client:
        def get(self, *a, **kw):
            return Bad()
    assert buscar_relacionados_wordpress("Tesla Optimus", "https://conexotech.com.br",
                                         request_client=Client()) == []
    assert buscar_relacionados_wordpress("Tesla Optimus", "https://staging.conexotech.com.br") == []


def test_idempotent_related_section_and_nonexistent_candidates():
    text = "O Optimus evoluiu na fábrica.\n"
    related = selecionar_relacionados("Optimus", POSTS)
    first = anexar_relacionados(text, related)
    second = anexar_relacionados(first, related)
    assert first == second
    assert inserir_links_contextuais(text, [], limite=2) == text
