"""
mkt_flow_p0.validator — Validação de links de afiliado (v3.11 unificado).
Cobre subdomínios variáveis do ML + shortlink /sec/. Case-insensitive.
Aceita `resolve` (alias do clássico) e `resolver_redirect`.

Estados: PASS / FAIL / UNKNOWN (v3.3). UNKNOWN nunca vira PASS.
Shopee: domínio reconhecido mas tracking não confirmável por este
validador → UNKNOWN (bloqueia divulgação até evidência real).

Pré-processamento externo: roda ANTES do LLM.
"""
import logging
import re
from urllib.parse import urlparse, parse_qs

import requests

logger = logging.getLogger("validator")

# Domínios aceitos — ML com subdomínios variáveis + shortlink /sec/
PADRAO_MELI = re.compile(
    r"^https?://([a-z0-9-]+\.)?mercadolivre\.com\.br(/.*)?$"
    r"|^https?://mercadolivre\.com/sec/.*$",
    re.IGNORECASE,
)
PADRAO_SHOPEE = re.compile(
    r"^https?://(s\.)?shopee\.com\.br(/.*)?$",
    re.IGNORECASE,
)

# Parâmetros de rastreamento do ML — confirmar nomes exatos no Portal do Afiliado
# antes de usar em produção; matt_word/matt_tool/tag são os mais comumente relatados.
TAGS_RASTREIO_MELI = {"matt_word", "matt_tool", "tag"}

# Sinais de página de produto (para ML-GENERIC-DESTINATION, cl. 3.1.2(d))
PADRAO_PRODUTO_ML = re.compile(r"(MLB\d+|/p/|/produto/|/sec/)", re.IGNORECASE)

HEADERS = {"User-Agent": "Mozilla/5.0 (MKT-Flow-P0 validator)"}


def _resolver_redirect(url: str, timeout: int = 5) -> str:
    """Segue redirect via HEAD para descobrir URL final. Nunca quebra: falha → URL original."""
    try:
        resp = requests.head(url, timeout=timeout, headers=HEADERS, allow_redirects=True)
        final = (resp.url or url).strip()
        logger.info(f"validator redirect resolvido: {url[:60]} -> {final[:60]}")
        return final
    except requests.Timeout:
        logger.warning(f"validator HEAD timeout após {timeout}s: {url[:80]}")
        return url
    except Exception as e:
        logger.warning(f"validator HEAD falhou ({e.__class__.__name__}): {url[:80]}")
        return url


def _destino_ml(url_final: str) -> str:
    """Classifica destino: 'produto' (anúncio específico) ou 'generico' (home/busca/categoria)."""
    if PADRAO_PRODUTO_ML.search(url_final or ""):
        return "produto"
    return "generico"


def validar_link_afiliado(url: str, timeout: int = 5, resolver_redirect: bool = True, **kwargs) -> dict:
    """Valida o link usando três estados: PASS, FAIL ou UNKNOWN.

    PASS  = evidência suficiente para considerar a validação aprovada.
    FAIL  = evidência suficiente de que a validação falhou.
    UNKNOWN = não há evidência suficiente para concluir.

    Regra de segurança: UNKNOWN nunca é convertido em PASS.
    `resolve` é aceito como alias de `resolver_redirect` (compat. clássico).
    """
    if "resolve" in kwargs and kwargs["resolve"] is not None:
        resolver_redirect = bool(kwargs["resolve"])

    url = (url or "").strip()
    if not url:
        return {
            "status_validacao": "FAIL",
            "valido": False,  # compatibilidade legada; usar status_validacao como autoridade
            "plataforma": "Desconhecida",
            "possui_tag_rastreio": False,
            "status": "URL vazia — validação reprovada.",
        }

    if PADRAO_MELI.match(url):
        plataforma = "Mercado Livre"
    elif PADRAO_SHOPEE.match(url):
        plataforma = "Shopee"
    else:
        return {
            "status_validacao": "FAIL",
            "valido": False,  # compatibilidade legada
            "plataforma": "Desconhecida",
            "possui_tag_rastreio": False,
            "status": "Domínio fora do padrão aceito.",
        }

    query = parse_qs(urlparse(url).query)

    if plataforma == "Mercado Livre":
        possui_tag = any(tag in query for tag in TAGS_RASTREIO_MELI)
        if not possui_tag:
            return {
                "status_validacao": "FAIL",
                "valido": False,  # compatibilidade legada
                "plataforma": plataforma,
                "possui_tag_rastreio": False,
                "status": "Domínio correto, mas SEM parâmetro de rastreamento — validação reprovada.",
            }

        url_final = _resolver_redirect(url, timeout=timeout) if resolver_redirect else url
        destino = _destino_ml(url_final)
        resultado = {
            "status_validacao": "PASS",
            "valido": True,  # compatibilidade legada
            "plataforma": plataforma,
            "possui_tag_rastreio": True,
            "status": "Domínio e parâmetro de rastreamento detectados.",
            "url_final": url_final,
            "destino": destino,
        }
        if destino != "produto":
            resultado["aviso"] = (
                "Destino não parece anúncio específico — ML-GENERIC-DESTINATION "
                "(cl. 3.1.2(d)) exige Link Especial de produto. Gere o link no portal do afiliado."
            )
        return resultado

    # Shopee: o método atual não possui evidência suficiente para confirmar o tracking.
    # NÃO assumir True. A ausência de uma checagem implementada é UNKNOWN, não PASS.
    url_final = _resolver_redirect(url, timeout=timeout) if resolver_redirect else url
    return {
        "status_validacao": "UNKNOWN",
        "valido": None,  # compatibilidade legada: None = desconhecido
        "plataforma": plataforma,
        "possui_tag_rastreio": None,
        "status": "Domínio Shopee reconhecido, mas o rastreamento não pode ser confirmado por este validador. Verificação necessária antes da divulgação.",
        "url_final": url_final,
        "destino": None,
    }


def resolve(url: str, timeout: int = 5) -> str:
    """Alias do clássico: resolve redirect e devolve URL final (sem validar)."""
    return _resolver_redirect(url, timeout=timeout)


def validar_lote(urls: list, timeout: int = 5, resolver_redirect: bool = False) -> list:
    """Valida várias URLs sem resolver redirect por padrão (rápido, sem rede extra)."""
    return [validar_link_afiliado(u, timeout=timeout, resolver_redirect=resolver_redirect) for u in (urls or [])]


def resumo_validacao(resultados: list) -> dict:
    """Agrega contagem por estado para dashboard/alertas."""
    agg = {"PASS": 0, "FAIL": 0, "UNKNOWN": 0}
    for r in resultados or []:
        est = (r or {}).get("status_validacao", "UNKNOWN")
        agg[est] = agg.get(est, 0) + 1
    return {"total": len(resultados or []), **agg}
