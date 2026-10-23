"""Produtor conservador do contrato editorial para noticias.

Aceita apenas fontes e claims previamente aprovados por processo externo.
Nunca cria PASS, fonte, data ou claim a partir do texto gerado por IA.
"""
from copy import deepcopy
from mkt_flow_p0.contrato_evidencias_noticia import avaliar_evidencias


def produzir_contrato_noticia(evidencias_aprovadas, texto_gerado):
    """Retorna snapshot verificavel ou None; nunca atesta semantica automaticamente."""
    if not isinstance(evidencias_aprovadas, dict) or not isinstance(texto_gerado, str):
        return None
    if not texto_gerado.strip():
        return None
    contrato = deepcopy(evidencias_aprovadas)
    if avaliar_evidencias(contrato).get("veredito") != "EVIDENCIAS_ESTRUTURADAS":
        return None
    # Cobertura textual conservadora: cada claim aprovado deve declarar
    # trecho exato (text), que precisa aparecer no artigo. Isso NAO detecta
    # alegacoes adicionais nem prova a veracidade da fonte.
    artigo = " ".join(texto_gerado.split()).casefold()
    for claim in contrato["claims"]:
        trecho = claim.get("text")
        if not isinstance(trecho, str) or not trecho.strip():
            return None
        if " ".join(trecho.split()).casefold() not in artigo:
            return None
    return contrato
