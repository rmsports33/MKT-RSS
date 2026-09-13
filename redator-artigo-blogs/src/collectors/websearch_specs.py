"""src.collectors.websearch_specs — busca de specs com cache em JSON.

Design honesto: nenhum scraping embutido. O chamador injeta `fetcher`
(função que recebe o nome do modelo e devolve specs) ou preenche
data/curated_specs.json manualmente (ficha do fabricante). Sem specs
verificadas, o gerador escreve "— não informado" em vez de inventar.
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger("websearch_specs")

BASE = Path(__file__).parent.parent.parent
CACHE_PATH = BASE / "data" / "search_cache.json"
CURATED_PATH = BASE / "data" / "curated_specs.json"


def _ler_cache() -> dict:
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _salvar_cache(cache: dict):
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"cache specs falhou: {e}")


def buscar_specs(modelo: str, categoria: str = "geral", fetcher=None, usar_cache: bool = True) -> dict:
    """Retorna {"specs": {...}, "fonte": "..."}.

    Ordem: cache → curated_specs.json → fetcher (se fornecido).
    Sem nenhuma fonte: {"specs": {}, "fonte": "", "aviso": ...}.
    """
    chave = f"{categoria}::{modelo}".lower()
    if usar_cache:
        hit = _ler_cache().get(chave)
        if hit:
            return {"specs": hit.get("specs", {}), "fonte": hit.get("fonte", ""), "origem": "cache"}
    try:
        curated = json.loads(CURATED_PATH.read_text(encoding="utf-8"))
        for item in curated if isinstance(curated, list) else []:
            if str(item.get("modelo", "")).lower() == modelo.lower():
                specs = dict(item.get("specs", {}))
                _salvar_cache({**_ler_cache(), chave: {"specs": specs, "fonte": item.get("fonte", "curated")}})
                return {"specs": specs, "fonte": item.get("fonte", "curated"), "origem": "curated"}
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning(f"curated_specs ilegível: {e}")
    if fetcher is not None:
        try:
            specs = dict(fetcher(modelo, categoria) or {})
            _salvar_cache({**_ler_cache(), chave: {"specs": specs, "fonte": "websearch"}})
            return {"specs": specs, "fonte": "websearch", "origem": "websearch"}
        except Exception as e:
            return {"specs": {}, "fonte": "", "erro": str(e)[:120]}
    return {"specs": {}, "fonte": "", "aviso": "sem fonte de specs — gerador usará '— não informado'"}
