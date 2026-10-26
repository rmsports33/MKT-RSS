"""Auditoria conservadora de cobertura textual após a IA.

Não certifica semântica, autenticidade de capturas ou autorização WP.
Só atesta que frases do texto gerado foram declaradas em claims aprovadas
e que o contrato já passou pelo lastro literal preexistente.
"""
import re
import unicodedata

from mkt_flow_p0.lastro_offline_noticia import auditar_lastro_offline


def _normalizar(texto):
    if not isinstance(texto, str):
        return ""
    return " ".join(unicodedata.normalize("NFKC", texto).casefold().split())


def _frases(texto):
    # Separação intencionalmente conservadora: não tenta inferir paráfrases.
    return [_normalizar(s) for s in re.split(r"(?<=[.!?])\s+|\n+", texto or "")
            if _normalizar(s)]


def auditar_cobertura_pos_ia(texto_gerado, contrato, capturas, referencias_traducao=None):
    """Só retorna COBERTURA_LITERAL quando há rastreio frase-a-frase.

    Resultados positivos são DIAGNÓSTICOS, nunca aprovação factual.
    """
    if not isinstance(texto_gerado, str) or not texto_gerado.strip():
        return {"veredito": "BLOQUEADO", "motivos": ["texto_gerado_ausente"]}
    lastro = auditar_lastro_offline(contrato, capturas)
    if lastro.get("veredito") != "LASTRO_LITERAL":
        return {"veredito": "BLOQUEADO",
                "motivos": ["lastro_insuficiente"] + lastro.get("motivos", [])}
    claims = [c.get("text", "") for c in contrato["claims"]]
    aceitas = {_normalizar(c) for c in claims if isinstance(c, str) and c.strip()}
    frases = _frases(texto_gerado)
    faltantes = [s for s in frases if s not in aceitas]
    # Referencias servem somente como fila de revisao semantica humana.
    referencias_traducao = referencias_traducao or {}
    ids = {c.get("id") for c in contrato["claims"]}
    candidatas = []
    nao_cobertas = []
    for frase in faltantes:
        refs = referencias_traducao.get(frase)
        if isinstance(refs, list) and refs and all(isinstance(i, str) and i in ids for i in refs):
            candidatas.append({"frase": frase, "claim_ids": refs})
        else:
            nao_cobertas.append(frase)
    veredito = ("BLOQUEADO" if nao_cobertas else
                "REVISAO_SEMANTICA_PENDENTE" if candidatas else "COBERTURA_LITERAL")
    return {
        "veredito": veredito,
        "motivos": (["frases_sem_claim_aprovada"] if nao_cobertas else
                    ["traducao_ou_parafrase_exige_revisao_humana"] if candidatas else []),
        "candidatas_traducao": candidatas,
        "sem_referencia": len(nao_cobertas),
        "frases": len(frases),
        "sem_correspondencia": len(faltantes),
        "certificacao_factual": False,
        "autoriza_wordpress": False,
    }
