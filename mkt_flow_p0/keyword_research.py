"""
mkt_flow_p0.keyword_research — Sugestão de keywords via Autocomplete do Google (grátis).
Sem API key, sem custo. Usado por seo.enriquecer_com_keywords (P1.5 GEO/AEO).
"""
import logging
import time
from urllib.parse import quote_plus

import requests

logger = logging.getLogger("keyword_research")

_AUTOCOMPLETE_URL = "https://suggestqueries.google.com/complete/search?client=firefox&q={q}"
_CACHE: dict = {}
TTL_SEGUNDOS = 3600
HEADERS = {"User-Agent": "Mozilla/5.0 (MKT-Flow-P0 keywords)"}


def _autocomplete(termo: str, timeout: int = 8) -> list:
    agora = time.time()
    entrada = _CACHE.get(termo)
    if entrada and (agora - entrada["ts"] < TTL_SEGUNDOS):
        return list(entrada["dados"])
    try:
        r = requests.get(_AUTOCOMPLETE_URL.format(q=quote_plus(termo)), timeout=timeout, headers=HEADERS)
        r.raise_for_status()
        dados = r.json()
        sugestoes = [str(s).strip() for s in (dados[1] if len(dados) > 1 else []) if str(s).strip()]
        _CACHE[termo] = {"ts": agora, "dados": sugestoes}
        return sugestoes
    except requests.Timeout:
        logger.warning("keyword autocomplete timeout")
        return []
    except Exception as e:
        logger.warning(f"keyword autocomplete falhou: {e}")
        return []


def sugerir_keywords_review(nome_produto: str, limit: int = 8, categoria: str = "") -> list:
    """Sugere keywords reais de review: nome + modificadores de compra (vale a pena, preço...)."""
    nome = (nome_produto or "").strip()
    if not nome:
        return []
    sementes = [nome, f"{nome} vale a pena", f"{nome} preço", f"{nome} review"]
    if categoria:
        sementes.append(f"{nome} {categoria}")
    vistas, out = set(), []
    for s in sementes:
        for kw in _autocomplete(s):
            k = kw.lower()
            if k not in vistas:
                vistas.add(k)
                out.append(kw)
            if len(out) >= limit:
                return out[:limit]
    # Fallback sem internet: modificadores padrão
    if not out:
        out = sementes[:limit]
    return out[:limit]


def limpar_cache():
    _CACHE.clear()
