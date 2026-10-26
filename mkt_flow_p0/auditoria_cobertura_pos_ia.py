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


def auditar_cobertura_pos_ia(texto_gerado, contrato, capturas):
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
    return {
        "veredito": "BLOQUEADO" if faltantes else "COBERTURA_LITERAL",
        "motivos": ["frases_sem_claim_aprovada"] if faltantes else [],
        "frases": len(frases),
        "sem_correspondencia": len(faltantes),
        "certificacao_factual": False,
        "autoriza_wordpress": False,
    }
