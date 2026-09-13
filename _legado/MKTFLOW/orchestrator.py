"""MKTFLOW.orchestrator — pipeline clássico ponta a ponta (v3.11 congelado).
Núcleo ativo: pipeline_p0.py + mkt_flow_p0.*. Aqui: run_pipeline + nomes
importáveis para patch nos testes legados. Persiste em affiliate_runs (B1)."""
import logging
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from MKTFLOW.db import get_db, init_db
from MKTFLOW.link_validator import validar_link_afiliado
from MKTFLOW.ml_client import consultar_api_publica_mercado_livre, extrair_item_id
from MKTFLOW.policy_engine import avaliar_politica
from MKTFLOW.wp_publisher import WPConfig, publicar_no_wordpress

logger = logging.getLogger("mktflow.orchestrator")


def run_pipeline(link: str, programa: str = "mercado_livre", fatos: dict = None,
                 publicar: bool = False, wp_config: WPConfig = None) -> dict:
    """Valida → ML → policy → (opcional) publica. Grava affiliate_runs. Retorna decisão."""
    init_db()
    link_id = str(uuid.uuid4())[:8]
    v = validar_link_afiliado(link)
    status_v = v.get("status_validacao", "UNKNOWN")
    item_id = extrair_item_id(link)
    dados_ml = consultar_api_publica_mercado_livre(item_id) if item_id else {}
    pol = avaliar_politica(programa, fatos or {})
    status_p = pol.get("status_politica", "UNKNOWN")

    decision = "BLOCK"
    motivo = ""
    if status_v == "FAIL":
        motivo = v.get("status", "validação FAIL")
    elif status_p == "FAIL":
        motivo = (pol.get("regras") or [{}])[0].get("evidencia", "policy FAIL")
    elif status_v != "PASS" or status_p != "PASS":
        motivo = "UNKNOWN — evidência insuficiente; verifique antes de divulgar"
    else:
        decision = "ALLOW"

    wp = {}
    if decision == "ALLOW" and publicar and wp_config is not None:
        titulo = (dados_ml.get("titulo") if isinstance(dados_ml, dict) else "") or "Oferta"
        wp = publicar_no_wordpress(wp_config, titulo, f"<p>{titulo}</p>", status_v, "publish")

    con = get_db()
    try:
        con.execute("INSERT INTO affiliate_runs (id, link, status, plataforma, policy, created_at)"
                    " VALUES (?,?,?,?,?,?)",
                    (link_id, link, status_v, v.get("plataforma", ""), status_p, datetime.now().isoformat()))
        con.commit()
    finally:
        con.close()
    return {"link_id": link_id, "status_validacao": status_v, "status_politica": status_p,
            "decision": decision, "motivo": motivo, "ml": dados_ml, "wp": wp,
            "plataforma": v.get("plataforma", "")}
