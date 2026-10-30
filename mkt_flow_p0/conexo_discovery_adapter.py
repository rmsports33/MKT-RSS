"""Exportacao estritamente somente leitura da fila RSS ao Conexo OS.

Nao inicializa tabelas, nao seleciona pautas, nao chama LLM/WordPress.
"""
import sqlite3
from pathlib import Path

from mkt_flow_p0 import cloud_db
from mkt_flow_p0.fila_pautas import DEFAULT_DB

CONTRACT_VERSION = "conexo-rss-discovery/1"
QUERY = """SELECT id, fonte, url, titulo, estado, pontuacao
           FROM rss_pautas WHERE estado=?
           ORDER BY pontuacao DESC, created_at DESC LIMIT ?"""


def _listar_sem_escrita(limite, db_path):
    if db_path is None and cloud_db.turso_enabled():
        result = cloud_db.turso_execute(QUERY, ("DESCOBERTA", limite))
        if "erro" in result:
            raise RuntimeError("Persistencia remota indisponivel: " + result["erro"])
        rows = result.get("rows", [])
    else:
        path = Path(db_path) if db_path is not None else DEFAULT_DB
        if not path.is_file():
            raise FileNotFoundError("Banco RSS nao inicializado: " + str(path))
        # URI read-only impede CREATE/UPDATE, inclusive se houver regressao.
        with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as con:
            rows = con.execute(QUERY, ("DESCOBERTA", limite)).fetchall()
    return [dict(zip(("id", "fonte", "url", "titulo", "estado", "pontuacao"), row))
            for row in rows]


def exportar_candidatos(limite=20, *, db_path=None):
    """Retorna candidatos rastreaveis; pontuacao e apenas heuristica."""
    if isinstance(limite, bool) or not isinstance(limite, int) or not 1 <= limite <= 100:
        raise ValueError("limite deve ser inteiro entre 1 e 100")
    pautas = _listar_sem_escrita(limite, db_path)
    return {
        "schema": CONTRACT_VERSION,
        "read_only": True,
        "approval": False,
        "publication_allowed": False,
        "candidates": [
            {
                "pauta_id": p["id"],
                "source_name": p["fonte"],
                "source_url": p["url"],
                "title": p["titulo"],
                "state": p["estado"],
                "ranking_hint": p["pontuacao"],
                "requires_fact_check": True,
                "requires_editorial_decision": True,
            }
            for p in pautas
        ],
    }
