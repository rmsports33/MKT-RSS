"""Adaptador fail-closed do EditorialContract v1.0 para noticias.

Nao importa o redator nem duplica modelos: recebe snapshot JSON do contrato.
A correspondencia semantica entre claims e artigo NAO e demonstrada aqui;
o retorno PASS somente atesta a estrutura das evidencias aprovadas.
"""
from datetime import datetime
from urllib.parse import urlparse


def _url_ok(url):
    try:
        p = urlparse(str(url or ""))
        return p.scheme == "https" and bool(p.netloc)
    except (TypeError, ValueError):
        return False


def _data_ok(value):
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return True
    except (TypeError, ValueError):
        return False


def avaliar_evidencias(contrato):
    """Valida rastreabilidade declarada. Nao valida veracidade externa."""
    erros = []
    if not isinstance(contrato, dict):
        return {"veredito": "BLOQUEADO", "motivos": ["contrato_ausente"]}
    if contrato.get("contract_version") != "1.0":
        erros.append("versao_contrato")
    if contrato.get("content_type") != "noticia":
        erros.append("tipo_conteudo")
    if contrato.get("status") != "PASS":
        erros.append("status_contrato")
    fontes = contrato.get("sources")
    claims = contrato.get("claims")
    if not isinstance(fontes, list) or not fontes:
        erros.append("fontes_ausentes")
        fontes = []
    if not isinstance(claims, list) or not claims:
        erros.append("claims_ausentes")
        claims = []
    ids = set()
    for f in fontes:
        if not isinstance(f, dict) or not f.get("id") or f["id"] in ids:
            erros.append("fonte_id_invalido")
            continue
        ids.add(f["id"])
        if (f.get("status") != "PASS" or f.get("pending") or
                not _url_ok(f.get("url")) or not _data_ok(f.get("retrieved_at"))):
            erros.append("fonte_nao_aprovada")
    claims_ids = set()
    for c in claims:
        if not isinstance(c, dict) or not c.get("id") or c["id"] in claims_ids:
            erros.append("claim_id_invalido")
            continue
        claims_ids.add(c["id"])
        if c.get("status") != "PASS" or c.get("pending") or c.get("heuristic"):
            erros.append("claim_nao_aprovado")
        referencias = c.get("evidence_ids")
        if not isinstance(referencias, list) or not referencias or not all(
                isinstance(i, str) and i in ids for i in referencias):
            erros.append("claim_sem_evidencia_aprovada")
    return {"veredito": "BLOQUEADO" if erros else "EVIDENCIAS_ESTRUTURADAS",
            "motivos": sorted(set(erros)), "claims": len(claims), "fontes": len(fontes)}
