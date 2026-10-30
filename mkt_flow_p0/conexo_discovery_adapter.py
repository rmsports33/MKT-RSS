"""Adaptador somente leitura: fila RSS -> candidatos para Conexo OS.

Nao seleciona pautas, nao chama LLM e nao escreve no WordPress.
"""
from mkt_flow_p0.fila_pautas import listar

CONTRACT_VERSION = "conexo-rss-discovery/1"


def exportar_candidatos(limite=20, *, db_path=None):
    """Retorna candidatos rastreaveis; pontuacao e apenas heuristica."""
    if isinstance(limite, bool) or not isinstance(limite, int) or not 1 <= limite <= 100:
        raise ValueError("limite deve ser inteiro entre 1 e 100")
    pautas = listar(estado="DESCOBERTA", limite=limite, db_path=db_path)
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
