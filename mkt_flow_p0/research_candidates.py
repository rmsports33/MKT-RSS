"""Pesquisa COMPLEMENTAR por RSS: somente candidatos, nunca facts certificados.

Reusa FEEDS_PADRAO e fetch_feed existentes; nao consulta novo provedor,
nao inventa citações nem atribui veracidade automatica aos excerpts.
"""
import html
import re
from urllib.parse import urlsplit

from mkt_flow_p0.related_posts import _tokens


def _mesmo_site_feed(url, feed_url):
    if not isinstance(url, str):
        return False
    try:
        u, f = urlsplit(url), urlsplit(feed_url)
        base = (f.hostname or "").removeprefix("www.")
        host = u.hostname or ""
        return (u.scheme == "https" and u.username is None and u.password is None
                and u.port in (None, 443) and not u.fragment
                and bool(base) and bool(u.path.strip("/"))
                and (host == base or host.endswith("." + base)))
    except ValueError:
        return False


def _resumo_pendente(text):
    if not isinstance(text, str):
        return ""
    clean = html.unescape(re.sub(r"<[^>]+>", " ", text))
    clean = re.sub(r"\s+", " ", clean).strip()[:340]
    return ("Resumo de RSS (alegações NÃO verificadas): " + clean
            if len(clean) >= 20 else "")


def descobrir_fontes_candidatas(titulo, url_original, *, fonte_original="",
                               feed_urls=None, fetcher=None, max_feeds=3,
                               limite=2):
    """Select up to two independently sourced candidate excerpts by title.

    Structural overlap is only a discovery heuristic. Human verification must
    distinguish corroboration from multiple outlets repeating the same report.
    """
    if not 1 <= max_feeds <= 4 or not 1 <= limite <= 2:
        raise ValueError("limite de pesquisa fora do escopo")
    if feed_urls is None or fetcher is None:
        from mkt_flow_p0.rss_ingestor import FEEDS_PADRAO, fetch_feed
        feed_urls = FEEDS_PADRAO if feed_urls is None else feed_urls
        fetcher = fetch_feed if fetcher is None else fetcher
    if not isinstance(feed_urls, dict):
        raise ValueError("feeds inválidos")
    source_host = urlsplit(url_original or "").hostname
    terms = _tokens(titulo)
    if not terms or not source_host:
        return {"sources": []}
    selections, seen_sites, visited_feeds = [], set(), 0
    for name, feed_url in feed_urls.items():
        if visited_feeds >= max_feeds or len(selections) >= limite:
            break
        host = urlsplit(feed_url).hostname
        if (not isinstance(name, str) or not isinstance(feed_url, str)
                or not host or host == source_host
                or host.removeprefix("www.") == source_host.removeprefix("www.")):
            continue
        visited_feeds += 1
        try:
            outcome = fetcher(feed_url, fonte=name, max_items=8, timeout=8)
        except (ValueError, TypeError, OSError):
            continue
        if not isinstance(outcome, dict) or not isinstance(outcome.get("itens"), list):
            continue
        best = None
        for item in outcome["itens"][:8]:
            if not isinstance(item, dict):
                continue
            url, heading = item.get("link"), item.get("titulo")
            if not _mesmo_site_feed(url, feed_url) or url == url_original:
                continue
            candidate = _tokens(heading)
            shared = terms & candidate
            if len(shared) < 2 or len(shared)/max(1,min(len(terms),len(candidate))) < 0.50:
                continue
            raw = _resumo_pendente(item.get("resumo"))
            if not raw:
                continue
            score = len(shared)
            if best is None or score > best[0]:
                best = (score, url, raw)
        if best is not None and host not in seen_sites:
            seen_sites.add(host)
            selections.append({"name": name[:100] + " (RSS pendente de apuração)",
                               "url": best[1], "facts": [best[2]]})
    return {"sources": selections}
