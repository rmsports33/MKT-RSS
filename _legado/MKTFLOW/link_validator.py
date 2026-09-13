"""MKTFLOW.link_validator — validador clássico (referência histórica, v3.11 congelado).
Núcleo ativo: mkt_flow_p0.validator. Mantido para os testes legados."""
import logging
import re
from urllib.parse import urlparse, parse_qs

import requests

logger = logging.getLogger("mktflow.link_validator")

PADRAO_MELI = re.compile(
    r"^https?://([a-z0-9-]+\.)?mercadolivre\.com\.br(/.*)?$"
    r"|^https?://mercadolivre\.com/sec/.*$",
    re.IGNORECASE,
)
PADRAO_SHOPEE = re.compile(
    r"^https?://(s\.)?shopee\.com\.br(/.*)?$",
    re.IGNORECASE,
)
TAGS_RASTREIO_MELI = {"matt_word", "matt_tool", "tag"}


def resolver_redirect(url: str, timeout: int = 5) -> str:
    try:
        r = requests.head(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
        return (r.url or url).strip()
    except Exception:
        return url


def validar_link_afiliado(url: str, timeout: int = 5, resolver: bool = False) -> dict:
    """Tri-state PASS/FAIL/UNKNOWN + legado `valido` (True/False/None)."""
    url = (url or "").strip()
    if PADRAO_MELI.match(url):
        plataforma = "Mercado Livre"
    elif PADRAO_SHOPEE.match(url):
        plataforma = "Shopee"
    else:
        return {"status_validacao": "FAIL", "valido": False, "plataforma": "Desconhecida",
                "possui_tag_rastreio": False, "status": "Domínio fora do padrão aceito."}
    query = parse_qs(urlparse(url).query)
    if plataforma == "Mercado Livre":
        if not any(t in query for t in TAGS_RASTREIO_MELI):
            return {"status_validacao": "FAIL", "valido": False, "plataforma": plataforma,
                    "possui_tag_rastreio": False,
                    "status": "Domínio correto, mas SEM parâmetro de rastreamento — validação reprovada."}
        final = resolver_redirect(url, timeout) if resolver else url
        return {"status_validacao": "PASS", "valido": True, "plataforma": plataforma,
                "possui_tag_rastreio": True, "status": "Domínio e parâmetro de rastreamento detectados.",
                "url_final": final}
    final = resolver_redirect(url, timeout) if resolver else url
    return {"status_validacao": "UNKNOWN", "valido": None, "plataforma": plataforma,
            "possui_tag_rastreio": None,
            "status": "Domínio Shopee reconhecido, mas o rastreamento não pode ser confirmado por este validador.",
            "url_final": final}
