"""MKTFLOW.ml_client — cliente API pública ML (clássico, v3.11 congelado).
Timeout 5s, retry 3x exponencial, cache TTL 300s, erros nunca cacheados.
Núcleo ativo equivalente: mkt_flow_p0.api_ml."""
import json
import logging
import re
import time
import urllib.request
import urllib.error

logger = logging.getLogger("mktflow.ml_client")

PADRAO_ITEM_ID = re.compile(r"^[A-Z]{3}\d+$")
_CACHE: dict = {}
TTL_PADRAO_SEGUNDOS = 300


def extrair_item_id(url: str) -> str:
    m = re.search(r"(MLB\d+)", url or "", re.IGNORECASE)
    return m.group(1).upper() if m else ""


def _get(url: str, timeout: int):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def consultar_api_publica_mercado_livre(item_id: str, timeout: int = 5, ttl: int = TTL_PADRAO_SEGUNDOS) -> dict:
    item_id = (item_id or "").strip().upper()
    agora = time.time()
    hit = _CACHE.get(item_id)
    if hit and (agora - hit["ts"] < ttl):
        dados = dict(hit["dados"])
        dados["origem"] = "cache"
        return dados
    if not PADRAO_ITEM_ID.match(item_id):
        return {"erro": f"item_id fora do padrão esperado (ex.: MLB123456789): '{item_id}'"}
    url = f"https://api.mercadolibre.com/items/{item_id}"
    ultimo_erro = ""
    for tentativa in range(3):
        try:
            data = _get(url, timeout)
            dados = {
                "titulo": data.get("title"),
                "preco": data.get("price"),
                "estoque": data.get("available_quantity"),
                "status": data.get("status"),
                "categoria_id": data.get("category_id"),
                "permalink": data.get("permalink"),
                "imagem": ((data.get("pictures") or [{}])[0].get("secure_url")),
                "seller_reputation": (data.get("seller") or {}).get("seller_reputation"),
            }
            if dados.get("titulo"):
                _CACHE[item_id] = {"ts": agora, "dados": dict(dados)}
            dados["origem"] = "api"
            return dados
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"erro": f"Item {item_id} não encontrado (404)"}
            ultimo_erro = f"Erro HTTP {e.code}"
        except TimeoutError:
            ultimo_erro = f"Consulta expirou após {timeout}s — tente novamente."
        except Exception as e:
            ultimo_erro = f"Falha na consulta: {str(e)[:100]}"
        time.sleep(0.5 * (2 ** tentativa))
    return {"erro": ultimo_erro or "Falha na consulta"}
