"""
mkt_flow_p0.cloud_db — Cliente Turso via HTTP (sem driver nativo).
Por que HTTP e não `libsql`: o pacote nativo não tem wheel para
Python 3.14 no Windows (falha de build 12/09/2026); HTTP usa só
`requests` (já dependência) e funciona igual no PC e no Actions.

Protocolo: POST {base}/v2/pipeline, Bearer token, baton null + close
por chamada (stateless, autocommit). Docs: turso.tech/sdk/http.
Env (lido sob demanda, sem side-effect no import):
  TURSO_DATABASE_URL  (libsql://... ou https://...turso.io)
  TURSO_AUTH_TOKEN
Sem os dois → chamador usa SQLite local (fallback).
"""
import logging
import os

import requests

logger = logging.getLogger("cloud_db")
TIMEOUT = 15


def turso_enabled() -> bool:
    return bool(os.getenv("TURSO_DATABASE_URL", "").strip()
                and os.getenv("TURSO_AUTH_TOKEN", "").strip())


def _base_url() -> str:
    raw = (os.getenv("TURSO_DATABASE_URL") or "").strip().rstrip("/")
    if raw.startswith("libsql://"):
        raw = "https://" + raw[len("libsql://"):]
    return raw + "/v2/pipeline"


def _encode_arg(v) -> dict:
    if v is None:
        return {"type": "null"}
    if isinstance(v, bool):
        return {"type": "integer", "value": str(int(v))}
    if isinstance(v, int):
        return {"type": "integer", "value": str(v)}
    if isinstance(v, float):
        return {"type": "float", "value": repr(v)}
    return {"type": "text", "value": str(v)}


def turso_execute(sql: str, args: tuple = (), timeout: int = TIMEOUT) -> dict:
    """Executa 1 statement. Retorna {"cols":[...], "rows":[[...]]} ou {"erro":...}."""
    try:
        resp = requests.post(
            _base_url(),
            headers={"Authorization": f"Bearer {os.getenv('TURSO_AUTH_TOKEN', '').strip()}",
                     "Content-Type": "application/json"},
            json={"requests": [{"type": "execute",
                                "stmt": {"sql": sql, "args": [_encode_arg(a) for a in (args or [])]}},
                               {"type": "close"}]},
            timeout=timeout,
        )
    except requests.Timeout:
        return {"erro": f"Turso timeout após {timeout}s"}
    except Exception as e:
        return {"erro": f"Turso indisponível: {str(e)[:120]}"}
    if resp.status_code == 401:
        return {"erro": "Turso 401 — token inválido ou expirado (gere outro no dashboard)"}
    if resp.status_code >= 400:
        return {"erro": f"Turso HTTP {resp.status_code}: {resp.text[:150]}"}
    try:
        data = resp.json()
        primeiro = (data.get("results") or [{}])[0]
        if primeiro.get("type") == "error":
            return {"erro": f"Turso SQL: {str(primeiro.get('error'))[:150]}"}
        result = (primeiro.get("response") or {}).get("result") or {}
        cols = [(c or {}).get("name", "") for c in (result.get("cols") or [])]
        rows = [[(cell or {}).get("value") for cell in (linha or [])] for linha in (result.get("rows") or [])]
        return {"cols": cols, "rows": rows,
                "affected": result.get("affected_row_count", 0)}
    except Exception as e:
        return {"erro": f"Resposta Turso ilegível: {str(e)[:120]}"}


def turso_init_rss() -> dict:
    """Cria tabela de dedup na nuvem (idempotente)."""
    r = turso_execute("""CREATE TABLE IF NOT EXISTS rss_vistos (
        id TEXT PRIMARY KEY, fonte TEXT, url TEXT, titulo_norm TEXT, created_at TEXT)""")
    if "erro" in r:
        return r
    return turso_execute("CREATE INDEX IF NOT EXISTS idx_rss_vistos_titulo ON rss_vistos(titulo_norm)")
