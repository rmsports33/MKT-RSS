"""Nota editorial 1..10 para pautas RSS e rascunhos WordPress.

Somente triagem. Não consulta audiência real, não verifica fontes, não aprova,
não agenda, não escreve no WordPress e não contorna o Gate Editorial.
"""
from datetime import date, datetime, timezone
from html import unescape
import re

PESOS = {
    "afinidade": 30,
    "publico_brasileiro": 25,
    "utilidade": 20,
    "atualidade": 15,
    "evergreen": 10,
}
VERSAO = "nota-editorial/1"
TEMAS = (
    "inteligencia artificial", "agente", "chatgpt", "android", "samsung", "galaxy",
    "iphone", "apple", "pixel", "celular", "smartphone", "notebook", "windows",
    "linux", "tv", "monitor", "bluetooth", "wifi", "wi-fi", "starlink",
    "satelite", "internet", "5g", "fibra", "operadora", "anatel", "seguranca",
    "ciber", "hacker", "antivirus", "privacidade", "google", "microsoft",
    "amd", "intel", "tecnologia", "jogo", "games", "console", "ssd", "usb",
)
FORA_DE_ESCOPO = ("mega-sena", "loteria", "horoscopo", "futebol", "celebridade")
BRASIL = ("brasil", "brasileiro", "anatel", "pix", "reais", "r$", "mercado livre",
          "magazine luiza", "defesa civil", "gov.br")
USO_PRATICO = ("como ", "qual ", "vale a pena", "escolher", "guia", "tutorial",
               "compar", "vs ", "configur", "instalar", "proteger", "dicas",
               "preco", "comprar", "melhor ", "evitar", "resolver")
OFERTA = ("promocao", "oferta", "desconto", "cupom", "baratinho", "deal", " off",
          "pre-venda")
NOTICIA = ("anuncia", "lanca", "revela", "apresenta", "vai ", "tera ", "inicia",
           "promete", "confirmou", "vazou", "insider")


def _limpo(value):
    if isinstance(value, dict):
        value = value.get("raw", value.get("rendered", ""))
    text = unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    return re.sub(r"\s+", " ", text).strip()


def _normal(text):
    import unicodedata
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in normalized if not unicodedata.combining(c))


def _data(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and len(value) >= 10:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            pass
    return None


def _limitar(value):
    return max(1, min(10, value))


def calcular_nota(criterios):
    """Pontua cinco critérios explícitos, inteiros 1..10. Sem números inventados."""
    if not isinstance(criterios, dict) or set(criterios) != set(PESOS):
        raise ValueError("Critérios devem conter exatamente os cinco eixos editoriais")
    for eixo, value in criterios.items():
        if type(value) is not int or not 1 <= value <= 10:
            raise ValueError("Critério inválido (1..10): " + eixo)
    centesimos = sum(criterios[eixo] * peso for eixo, peso in PESOS.items())
    nota = (centesimos + 50) // 100  # arredondamento meio para cima
    return {"nota": int(nota), "pontuacao": int(nota) * 10,
            "media_ponderada": round(centesimos / 100, 2),
            "criterios": dict(criterios), "pesos": dict(PESOS),
            "faixa": faixa(nota), "versao": VERSAO}


def faixa(nota):
    if nota >= 9:
        return "PRIORIDADE_MAXIMA"
    if nota >= 7:
        return "ALTA"
    if nota >= 5:
        return "INTERMEDIARIA"
    return "BAIXA"


def sugerir_criterios(item, *, referencia=None):
    """Sugestão provisória por assunto e idade; NÃO mede tráfego nem volume de busca."""
    if not isinstance(item, dict):
        raise ValueError("Item inválido")
    titulo = _limpo(item.get("titulo", item.get("title")))
    resumo = _limpo(item.get("resumo", item.get("excerpt", "")))
    if not titulo:
        raise ValueError("Título obrigatório")
    texto = _normal(titulo + " " + resumo)
    assunto = _normal(titulo)
    if any(x in assunto for x in FORA_DE_ESCOPO):
        return {eixo: 1 for eixo in PESOS}
    elif any(x in texto for x in TEMAS) or re.search(r"\b(?:ia|llm)\b", texto):
        afinidade = 9
    else:
        afinidade = 5
    if any(x in texto for x in BRASIL):
        publico = 9
    elif any(x in texto for x in ("eua", "dolar", "us$", "walmart", "reino unido")):
        publico = 4
    elif afinidade >= 8:
        publico = 7
    else:
        publico = 5
    pratica = any(x in assunto for x in USO_PRATICO)
    utilidade = 9 if pratica else (8 if any(x in texto for x in
                    ("golpe", "privacidade", "fraude", "protecao", "seguranca",
                     "economia", "acesso", "rural")) else 6)
    oferta = any(x in assunto for x in OFERTA)
    noticia = any(x in assunto for x in NOTICIA)
    evergreen = 2 if oferta else (9 if pratica else (4 if noticia else 6))
    referencia = _data(referencia) or datetime.now(timezone.utc).date()
    publicado = _data(item.get("published") or item.get("modified")
                      or item.get("date"))
    if publicado:
        idade = (referencia - publicado).days
        if idade < 0:
            atualidade = 4  # data futura/ambígua não comprova atualidade
        elif idade <= 7:
            atualidade = 9
        elif idade <= 30:
            atualidade = 7
        elif idade <= 90:
            atualidade = 5
        else:
            atualidade = 3
        if oferta and idade > 7:
            atualidade = 1
    else:
        atualidade = 5  # neutro quando a fonte não informa a data
    if "[teste" in assunto or "nao publicar" in assunto:
        return {eixo: 1 for eixo in PESOS}
    return {
        "afinidade": afinidade, "publico_brasileiro": publico,
        "utilidade": utilidade, "atualidade": atualidade,
        "evergreen": evergreen,
    }


def avaliar_pauta(item, *, criterios=None, referencia=None):
    """Uma nota + proveniência. Avaliação humana exige cinco critérios explícitos."""
    estimativa = criterios is None
    dados = sugerir_criterios(item, referencia=referencia) if estimativa else criterios
    report = calcular_nota(dados)
    report["origem"] = "HEURISTICA_PROVISORIA" if estimativa else "REVISAO_EDITORIAL"
    report["audiencia_medida"] = False
    report["publicacao_autorizada"] = False
    return report
