"""Strict offline adapter for the editorial pilot.

No arbitrary callback, no provider key and no WordPress client. This is NOT an
OS sandbox; real providers require independently enforced network isolation.
"""
from __future__ import annotations
import hashlib
import re
from mkt_flow_p0.editorial_negative_checks import check_rendered

def run_offline(source: str, *, approved_snapshot: bool = False) -> dict:
    base = {"status": "BLOQUEADO", "verificacao_factual": "NAO_VERIFICADO",
            "escreveu": False, "wordpress": "PROIBIDO", "custo_usd": 0}
    if not approved_snapshot or not isinstance(source, str) or not source.strip():
        return {**base, "motivo": "snapshot_nao_aprovado"}
    if len(source) > 20000:
        return {**base, "motivo": "limite_de_entrada"}
    # Deterministic rendition of the supplied text only; no claims generated.
    from html import escape
    clean = source.strip()
    title = "Prévia documental não certificada"
    html = "<article><h1>" + escape(title) + "</h1><p>" + escape(clean) + "</p></article>"
    fields = {"titulo_seo": title, "texto_markdown": clean, "meta_description": "",
              "slug": "", "tags": [], "json_ld": {}}
    audit = check_rendered(source, html, fields)
    return {**base, "status": "PREVIA_DOCUMENTAL",
            "motivo": "revisao_humana_obrigatoria",
            "fonte_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "html": html, "campos": fields, "auditoria": audit}

def authorize_provider(*args, **kwargs):
    """A real provider adapter is not available until network/cost isolation is certified."""
    return {"status": "BLOQUEADO", "motivo": "isolamento_de_rede_nao_certificado",
            "verificacao_factual": "NAO_VERIFICADO", "escreveu": False}
