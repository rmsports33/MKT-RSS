"""Candidate sourcing is safe, deterministic and explicitly unverified."""
from mkt_flow_p0.research_candidates import descobrir_fontes_candidatas
from mkt_flow_p0.editorial_identity import normalizar_fontes_complementares

FEEDS = {
    "canaltech": "https://canaltech.com.br/rss/",
    "9to5google": "https://9to5google.com/feed/",
    "sammobile": "https://www.sammobile.com/feed/"
}
ORIGINAL = "https://tecnoblog.net/noticias/android-ia"


def _fake_feed(url, *, fonte, max_items, timeout):
    assert max_items == 8 and timeout == 8
    if fonte == "canaltech":
        return {"itens": [
            {"titulo": "Android IA traz novos recursos para celular",
             "link": "https://canaltech.com.br/android/android-ia-novos-recursos/",
             "resumo": "<p>Fabricante relatou novidades em aplicativos para Android.</p>"},
            {"titulo": "Android IA adiciona recurso estranho",
             "link": "https://fake.example/injecao",
             "resumo": "Resumo que não pertence à fonte do RSS e é rejeitado."}
        ]}
    if fonte == "9to5google":
        return {"itens": [
            {"titulo": "New Android AI features for phone apps",
             "link": "https://9to5google.com/2026/11/06/android-ai-features/",
             "resumo": "The publication reports AI functions in Android applications."}
        ]}
    return {"erro": "indisponivel"}


def test_candidates_have_real_url_and_explicitly_unverified_excerpt():
    p = descobrir_fontes_candidatas(
        "Android IA: novos recursos para celular", ORIGINAL,
        feed_urls=FEEDS, fetcher=_fake_feed, max_feeds=3)
    assert len(p["sources"]) >= 1
    assert all(x["url"].startswith("https://") for x in p["sources"])
    assert all("NÃO verificadas" in x["facts"][0] for x in p["sources"])
    assert all("fake.example" not in x["url"] for x in p["sources"])
    assert len(normalizar_fontes_complementares(p)) == len(p["sources"])


def test_unrelated_news_is_not_misrepresented_as_corroboration():
    p = descobrir_fontes_candidatas(
        "Patente sobre bateria nuclear de silicio",
        ORIGINAL, feed_urls=FEEDS, fetcher=_fake_feed)
    assert p == {"sources": []}


def test_no_extra_calls_when_two_sources_found():
    calls = []
    def fetch(*args, **kwargs):
        calls.append(args[0])
        name = kwargs["fonte"]
        u = FEEDS[name]
        h = "www.sammobile.com" if name == "sammobile" else u.split("/")[2]
        return {"itens": [{
            "titulo": "Android IA novos recursos para celular",
            "link": f"https://{h}/android-novos-recursos/",
            "resumo": "Foi relatada uma novidade tecnológica relacionada ao Android."}]}
    p = descobrir_fontes_candidatas(
        "Android IA: novos recursos para celular", ORIGINAL,
        feed_urls=FEEDS, fetcher=fetch, limite=2)
    assert len(p["sources"]) == 2
    assert len(calls) == 2


def test_invalid_candidate_limit_fails_closed():
    import pytest
    with pytest.raises(ValueError):
        descobrir_fontes_candidatas("Android", ORIGINAL, max_feeds=100,
                                   feed_urls=FEEDS, fetcher=_fake_feed)


def test_http_or_cross_domain_feed_entry_not_accepted():
    def bogus(*args, **kwargs):
        return {"itens": [
            {"titulo": "Android IA: novos recursos para celular",
             "link": "http://canaltech.com.br/sem-https",
             "resumo": "Noticia alternativa divulgada em canal nao seguro."},
            {"titulo": "Android IA: novos recursos para celular",
             "link": "https://example.net/nao-confiavel",
             "resumo": "Noticia de dominio nao correspondente ao feed."}]}
    result = descobrir_fontes_candidatas("Android IA: novos recursos para celular",
                                         ORIGINAL, feed_urls=FEEDS, fetcher=bogus)
    assert result == {"sources": []}
