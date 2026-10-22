"""Verificacoes conservadoras apos a geracao por IA."""

import re
import unicodedata


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in texto if not unicodedata.combining(c)).lower()


def validar_saida(texto_fonte, texto_gerado):
    motivos = []
    fonte = _normalizar(texto_fonte)
    gerado = _normalizar(texto_gerado)

    alegacoes = [
        r"\b(?:nos|nossa equipe)\s+(?:testamos|avaliamos|experimentamos)\b",
        r"\b(?:testamos|avaliamos|experimentamos)\b",
        r"\b(?:em nossos testes|nosso laboratorio)\b",
    ]

    for padrao in alegacoes:
        if re.search(padrao, gerado):
            motivos.append("alegacao_de_teste_proprio")
            break

    valores = r"(?<!\w)(?:R\$\s*|US\$\s*|\$\s*)?\d+(?:[.,]\d+)*(?:\s*%|\s*(?:GB|TB|Hz|mAh))?(?!\w)"

    numeros_fonte = set(re.findall(valores, fonte, flags=re.I))
    numeros_gerados = set(re.findall(valores, gerado, flags=re.I))

    novos = sorted(numeros_gerados - numeros_fonte)
    if novos:
        motivos.append("numeros_sem_correspondencia_na_fonte")

    return {
        "veredito": "BLOQUEADO" if motivos else "SEM_ALERTAS",
        "motivos": motivos,
        "numeros_novos": novos,
    }
