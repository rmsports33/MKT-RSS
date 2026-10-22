"""Verificações conservadoras de evidências numéricas e alegações após IA.

SEM_ALERTAS significa ausência dos alertas implementados, não comprovação factual.
"""
import re
import unicodedata

MESES = {"janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5,
         "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
         "outubro": 10, "novembro": 11, "dezembro": 12}
NUMERO = re.compile(r"(?<!\w)(?:r\$\s*|us\$\s*|\$\s*)?\d+(?:[.,]\d+)*(?:\s*(?:reais|%|gb|tb|hz|mah))?(?!\w)", re.I)
PRODUTO = re.compile(r"\b(?:modelo|produto)\s+[a-z0-9]+\b", re.I)
PRECO = re.compile(r"(?<!\w)(?:r\$\s*\d[\d.,]*|\d[\d.,]*\s+reais)\b", re.I)


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in texto if not unicodedata.combining(c)).lower()


def _datas(texto):
    def converter(m):
        dia, mes, ano = m.groups()
        return f"{int(dia):02d}/{MESES[mes]:02d}/{ano}"
    meses = "|".join(MESES)
    return re.sub(rf"\b(\d{{1,2}})\s+de\s+({meses})\s+de\s+(\d{{4}})\b",
                  converter, texto)


def _numeros(texto):
    saida = set()
    for m in NUMERO.finditer(texto):
        valor = m.group().strip().lower()
        monetario = valor.startswith("r$") or valor.endswith("reais")
        if monetario:
            valor = re.sub(r"^(?:r\$\s*)|(?:\s+reais)$", "", valor).strip()
            saida.add("brl:" + valor)
        else:
            saida.add(re.sub(r"\s+", " ", valor))
    return saida


def _associacoes(texto):
    """Valores próximos a rótulos explícitos, sem inferir relações semânticas."""
    marcas = list(PRODUTO.finditer(texto))
    resultado = {}
    for i, marca in enumerate(marcas):
        fim = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
        trecho = texto[marca.end():fim]
        resultado.setdefault(marca.group(), set()).update(_numeros(trecho))
    return resultado


def validar_saida(texto_fonte, texto_gerado):
    fonte = _datas(_normalizar(texto_fonte))
    gerado = _datas(_normalizar(texto_gerado))
    motivos = []

    # Atribuição inequívoca a terceiros pode conter citação em primeira pessoa.
    citacao = bool(re.search(r"\b(?:segundo|conforme)\s+a\s+empresa\b", gerado))
    citacao_confirmada = citacao and bool(re.search(r"\b(?:testamos|avaliamos|experimentamos)\b", fonte))
    alegacao = bool(re.search(
        r"\b(?:testamos|avaliamos|experimentamos|nossa equipe\s+"
        r"(?:testou|avaliou|experimentou)|em nossos testes|nosso laboratorio)\b",
        gerado))
    if alegacao and not citacao_confirmada:
        motivos.append("alegacao_de_teste_proprio")

    novos = sorted(_numeros(gerado) - _numeros(fonte))
    if novos:
        motivos.append("numeros_sem_correspondencia_na_fonte")

    fontes = _associacoes(fonte)
    gerados = _associacoes(gerado)
    for produto, numeros in gerados.items():
        if produto in fontes and numeros - fontes[produto]:
            if "associacao_produto_valor_inconsistente" not in motivos:
                motivos.append("associacao_produto_valor_inconsistente")

    return {
        "veredito": "BLOQUEADO" if motivos else "SEM_ALERTAS",
        "motivos": motivos,
        "numeros_novos": novos,
    }
