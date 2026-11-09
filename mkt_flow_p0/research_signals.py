"""Opt-in research adapters. Missing provider is visible, never invented demand."""
from datetime import datetime, timezone


def autocomplete(term, *, limit=8):
    from mkt_flow_p0.keyword_research import pesquisar_keywords
    return pesquisar_keywords(term, limit)


def trends(terms, *, provider=None):
    """Bounded single comparison, no retries/browser fallback installed implicitly.

    Raw provider output remains separate from the reviewed 7-day input contract.
    Neither a raw snapshot nor an import certifies editorial approval.
    """
    if not 1 <= len(terms) <= 5 or any(not str(t).strip() for t in terms):
        raise ValueError("Trends exige 1..5 termos")
    observed = datetime.now(timezone.utc).isoformat()
    if provider is None:
        try:
            from trendspyg import download_google_trends_explore, download_google_trends_comparison
        except ImportError:
            return {"source": "trends", "status": "PROVEDOR_NAO_INSTALADO",
                    "observed_at": observed, "geo": "BR", "search_volume": None}
        provider = download_google_trends_comparison if len(terms) > 1 else download_google_trends_explore
    try:
        raw = provider(terms if len(terms) > 1 else terms[0],
                       geo="BR", timeframe="now 7-d", engine="http")
        return {"source": "trends", "status": "SNAPSHOT_NAO_VALIDADO", "geo": "BR",
                "observed_at": observed, "terms": terms, "raw": raw, "search_volume": None}
    except Exception as exc:
        # Do not leak a provider's response/cookies/credentials in logs.
        return {"source": "trends", "status": "INDISPONIVEL", "geo": "BR",
                "observed_at": observed, "error_type": type(exc).__name__, "search_volume": None}
