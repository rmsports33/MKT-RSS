"""
mkt_flow_p0.alerts — Alertas de links (P1.4): quebrados (404) e sem estoque.
HEAD leve com timeout; consulta de estoque via api_ml (mockável nos testes).
Severidade: CRITICAL (404/bloqueio) > HIGH (sem estoque) > OK.
"""
import logging
import time

import requests

logger = logging.getLogger("alerts")

HEADERS = {"User-Agent": "Mozilla/5.0 (MKT-Flow-P0 alerts)"}


def _check_url_head(url: str, timeout: int = 8) -> dict:
    """HEAD na URL. Retorna {url, http_code, ok, elapsed_ms} ou {"erro":...}."""
    ini = time.time()
    try:
        r = requests.head((url or "").strip(), timeout=timeout, headers=HEADERS, allow_redirects=True)
        return {"url": url, "http_code": r.status_code, "ok": r.status_code < 400, "elapsed_ms": int((time.time() - ini) * 1000)}
    except requests.Timeout:
        return {"url": url, "http_code": 0, "ok": False, "elapsed_ms": int((time.time() - ini) * 1000), "erro": f"timeout após {timeout}s"}
    except Exception as e:
        return {"url": url, "http_code": 0, "ok": False, "elapsed_ms": 0, "erro": str(e)[:120]}


def check_link(url: str, item_id: str = "", timeout: int = 8) -> dict:
    """Checa 1 link: HEAD + estoque (se item_id ML)."""
    head = _check_url_head(url, timeout=timeout)
    if not head.get("ok"):
        return {"url": url, "severidade": "CRITICAL", "motivo": "link_quebrado", "detalhe": head}

    if item_id:
        try:
            from mkt_flow_p0.api_ml import consultar_api_publica_mercado_livre
            dados = consultar_api_publica_mercado_livre(item_id, timeout=timeout)
        except Exception as e:
            return {"url": url, "severidade": "UNKNOWN", "motivo": "estoque_nao_verificado", "detalhe": str(e)[:100]}
        if "erro" in dados:
            return {"url": url, "severidade": "HIGH", "motivo": "produto_indisponivel", "detalhe": dados["erro"]}
        if (dados.get("estoque") or 0) <= 0:
            return {"url": url, "severidade": "HIGH", "motivo": "sem_estoque", "detalhe": dados}
        return {"url": url, "severidade": "OK", "motivo": "link_ok", "detalhe": {"estoque": dados.get("estoque"), "preco": dados.get("preco")}}
    return {"url": url, "severidade": "OK", "motivo": "link_ok", "detalhe": head}


def check_all(itens: list, timeout: int = 8) -> dict:
    """Checa lista [{url, item_id?}]. Retorna {total, criticos, sem_estoque, ok, resultados}."""
    resultados = [check_link((it or {}).get("url", ""), (it or {}).get("item_id", ""), timeout) for it in (itens or [])]
    return {
        "total": len(resultados),
        "criticos": sum(1 for r in resultados if r["severidade"] == "CRITICAL"),
        "sem_estoque": sum(1 for r in resultados if r["severidade"] == "HIGH"),
        "ok": sum(1 for r in resultados if r["severidade"] == "OK"),
        "resultados": resultados,
    }


def checar_links_quebrados(urls: list, timeout: int = 8) -> list:
    """Atalho P1: só os quebrados (para alerta CRITICAL)."""
    return [r for r in check_all([{"url": u} for u in (urls or [])], timeout)["resultados"] if r["severidade"] == "CRITICAL"]


def checar_estoque(item_ids: list, timeout: int = 8) -> list:
    """Atalho P1: estoque de itens ML (para alerta HIGH)."""
    from mkt_flow_p0.api_ml import consultar_api_publica_mercado_livre
    out = []
    for iid in item_ids or []:
        dados = consultar_api_publica_mercado_livre(iid, timeout=timeout)
        out.append({"item_id": iid, "estoque": dados.get("estoque"), "erro": dados.get("erro")})
    return out
