"""Auditoria offline de lastro textual de claims; nao consulta rede.

O pacote deve vir de um revisor externo confiavel, nunca do RSS/LLM.
A coincidencia literal nao comprova autenticidade nem semantica.
"""
from mkt_flow_p0.contrato_evidencias_noticia import avaliar_evidencias


def auditar_lastro_offline(contrato, capturas):
    """Bloqueia claims sem trecho literal em capturas externas fornecidas."""
    motivos = []
    if avaliar_evidencias(contrato).get("veredito") != "EVIDENCIAS_ESTRUTURADAS":
        return {"veredito": "BLOQUEADO", "motivos": ["contrato_invalido"]}
    if not isinstance(capturas, dict):
        return {"veredito": "BLOQUEADO", "motivos": ["capturas_ausentes"]}
    fontes = {f["id"]: f for f in contrato["sources"]}
    for claim in contrato["claims"]:
        trecho = claim.get("text")
        if not isinstance(trecho, str) or not trecho.strip():
            motivos.append("claim_sem_texto")
            continue
        for source_id in claim["evidence_ids"]:
            captura = capturas.get(source_id)
            if not isinstance(captura, dict):
                motivos.append("captura_ausente")
                continue
            if captura.get("url") != fontes[source_id]["url"]:
                motivos.append("url_captura_divergente")
            corpo = captura.get("texto")
            if not isinstance(corpo, str) or not corpo.strip():
                motivos.append("texto_captura_ausente")
            elif " ".join(trecho.split()).casefold() not in " ".join(corpo.split()).casefold():
                motivos.append("claim_sem_lastro_literal")
    return {"veredito": "BLOQUEADO" if motivos else "LASTRO_LITERAL",
            "motivos": sorted(set(motivos))}
