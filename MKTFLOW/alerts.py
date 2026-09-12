"""MKTFLOW.alerts — alertas clássicos (v3.11 congelados). HEAD + estoque ML."""
import logging
import time

import requests

try:
    from .ml_client import consultar_api_publica_mercado_livre
except ImportError:  # testes importam como pacote raiz
    from ml_client import consultar_api_publica_mercado_livre  # type: ignore

logger = logging.getLogger("mktflow.alerts")
HEADERS = {"User-Agent": "Mozilla/5.0"}


def _check_url_head(url: str, timeout: int = 8) -> dict:
    ini = time.time()
    try:
        r = requests.head((url or "").strip(), timeout=timeout, headers=HEADERS, allow_redirects=True)
        return {"url": url, "http_code": r.status_code, "ok": r.status_code < 400,
                "elapsed_ms": int((time.time() - ini) * 1000)}
    except Exception as e:
        return {"url": url, "http_code": 0, "ok": False, "elapsed_ms": 0, "erro": str(e)[:100]}


def check_link(url: str, item_id: str = "", timeout: int = 8) -> dict:
    head = _check_url_head(url, timeout=timeout)
    if not head.get("ok"):
        return {"url": url, "severidade": "CRITICAL", "motivo": "link_quebrado", "detalhe": head}
    if item_id:
        dados = consultar_api_publica_mercado_livre(item_id, timeout=timeout)
        if "erro" in dados:
            return {"url": url, "severidade": "HIGH", "motivo": "produto_indisponivel", "detalhe": dados["erro"]}
        if (dados.get("estoque") or 0) <= 0:
            return {"url": url, "severidade": "HIGH", "motivo": "sem_estoque", "detalhe": dados}
    return {"url": url, "severidade": "OK", "motivo": "link_ok", "detalhe": head}


def check_all(itens: list, timeout: int = 8) -> dict:
    resultados = [check_link((it or {}).get("url", ""), (it or {}).get("item_id", ""), timeout) for it in (itens or [])]
    return {"total": len(resultados),
            "criticos": sum(1 for r in resultados if r["severidade"] == "CRITICAL"),
            "ok": sum(1 for r in resultados if r["severidade"] == "OK"),
            "resultados": resultados}
