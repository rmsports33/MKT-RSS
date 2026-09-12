"""
mkt_flow_p0.api_ml — Cliente API pública Mercado Livre
Implementa MKT_Flow_3_0-1708-2251_v3.6.md:503-548 com retry+cache
Pré-processamento externo: roda ANTES do LLM.
"""
import re
import time
import json
import logging
from typing import Dict

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("api_ml")

PADRAO_ITEM_ID = re.compile(r"^[A-Z]{3}\d+$")
_CACHE: Dict[str, dict] = {}
TTL_PADRAO_SEGUNDOS = 300

# Sessão com retry para erros de rede (não para 404)
_session = requests.Session()
_retry = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
_session.mount("https://", HTTPAdapter(max_retries=_retry))


def consultar_api_publica_mercado_livre(
    item_id: str, timeout: int = 5, ttl: int = TTL_PADRAO_SEGUNDOS, usar_cache: bool = True
) -> dict:
    """
    Busca dados do produto. Retorna dict com titulo/preco/estoque/status ou {"erro":...}.
    Nunca cacheia erro. TTL 5min por padrão.
    """
    item_id = (item_id or "").strip().upper()
    agora = time.time()

    if usar_cache and item_id in _CACHE:
        entrada = _CACHE[item_id]
        if agora - entrada["timestamp"] < ttl:
            dados = dict(entrada["dados"])
            dados["origem"] = "cache"
            logger.info(f"ML cache hit {item_id}")
            return dados

    if not PADRAO_ITEM_ID.match(item_id):
        return {"erro": f"item_id fora do padrão esperado (ex.: MLB123456789): '{item_id}'"}

    url = f"https://api.mercadolibre.com/items/{item_id}"
    try:
        resp = _session.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 404:
            return {"erro": f"Item {item_id} não encontrado (404)"}
        resp.raise_for_status()
        data = resp.json()
        dados = {
            "titulo": data.get("title"),
            "preco": data.get("price"),
            "estoque": data.get("available_quantity"),
            "status": data.get("status"),
            "categoria_id": data.get("category_id"),
            "imagens": [p.get("secure_url") or p.get("url") for p in (data.get("pictures") or [])][:3],
            "vendedor_id": (data.get("seller") or {}).get("id"),
        }
        # só cacheia sucesso com titulo
        if dados.get("titulo"):
            _CACHE[item_id] = {"timestamp": agora, "dados": dict(dados)}
        dados["origem"] = "api"
        return dados
    except requests.Timeout:
        return {"erro": f"Consulta expirou após {timeout}s — tente novamente."}
    except requests.HTTPError as e:
        return {"erro": f"Erro HTTP {e.response.status_code} — item pode não existir ou estar indisponível."}
    except Exception as e:
        # Nunca expor stack completo em produção; loga mas retorna mensagem genérica
        logger.warning(f"ML api falhou {item_id}: {e}")
        return {"erro": f"Falha na consulta: {str(e)[:120]}"}


def _limpar_cache():
    _CACHE.clear()
