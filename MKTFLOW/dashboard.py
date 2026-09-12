"""MKTFLOW.dashboard — consolidado clássico (v3.11 congelado)."""
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("mktflow.dashboard")
DB = Path(__file__).parent / "mkt_flow.db"


def _rows(sql: str, params=()):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in con.execute(sql, params).fetchall()]
    except Exception:
        rows = []
    con.close()
    return rows


def get_consolidated_metrics() -> dict:
    runs = _rows("SELECT * FROM affiliate_runs ORDER BY created_at DESC LIMIT 200")
    pubs = _rows("SELECT * FROM link_publications ORDER BY created_at DESC LIMIT 200")
    agrupado: dict = {}
    for p in pubs:
        k = p.get("plataforma", "?")
        agrupado[k] = agrupado.get(k, 0) + 1
    return {"total_runs": len(runs), "total_publicacoes": len(pubs),
            "por_plataforma": agrupado, "atualizado_em": datetime.now().isoformat()}


def get_product_performance_matrix() -> dict:
    """Matriz produto(plataforma) x métricas a partir das publicações."""
    pubs = _rows("SELECT * FROM link_publications ORDER BY created_at DESC LIMIT 500")
    matriz: dict = {}
    for p in pubs:
        prod = (p.get("link_original") or "?")[:60]
        plat = p.get("plataforma", "?")
        matriz.setdefault(prod, {}).setdefault(plat, 0)
        matriz[prod][plat] += 1
    return {"matriz": matriz, "produtos": len(matriz)}


def generate_html_dashboard(metrics: dict = None) -> str:
    m = metrics or get_consolidated_metrics()
    linhas = "".join(f"<li>{k}: {v}</li>" for k, v in (m.get("por_plataforma") or {}).items())
    return (f"<!DOCTYPE html><html lang='pt-BR'><head><meta charset='UTF-8'>"
            f"<title>MKT Flow — Dashboard</title></head><body>"
            f"<h1>MKT Flow — {m.get('total_runs', 0)} runs · {m.get('total_publicacoes', 0)} publicações</h1>"
            f"<ul>{linhas or '<li>Sem dados</li>'}</ul></body></html>")
