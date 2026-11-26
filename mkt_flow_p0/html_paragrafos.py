"""Recupera a estrutura de parágrafos de um HTML editorial já renderizado.

Motivo (rascunho #9900, 22/11/2026): o renderizador antigo emitia um `<p>` por
linha do arquivo Markdown e fechava a lista a cada linha. O texto salvo no
WordPress ficou com frases cortadas a cada 78 colunas, listas numeradas
recomeçando em 1 e continuação de item fora do `<li>`.

`reparar_paragrafos` desfaz apenas essa fragmentação: junta blocos que são a
mesma frase, junta listas seguidas do mesmo tipo e devolve para dentro do item
a continuação que caiu fora. Não reescreve, não reordena e não remove palavra.
"""
import html as _html
import re

_TERMINA = (".", "!", "?", ":", '"', ")", "…", "]", "”")

_BLOCO = re.compile(
    r"<p\b[^>]*>.*?</p>"
    r"|<(ol|ul)\b[^>]*>.*?</\1>"
    r"|<h([1-6])\b[^>]*>.*?</h\2>"
    r"|<table\b[^>]*>.*?</table>"
    r"|<div\b[^>]*>.*?</div>"
    r"|<figure\b[^>]*>.*?</figure>"
    r"|<hr\b[^>]*/?>"
    r"|<!--.*?-->",
    re.S | re.I,
)

_INICIA_MINUSCULA = re.compile(r"^[a-záàâãéêíóôõúüç]")


def _tag(bloco: str) -> str:
    m = re.match(r"<([a-zA-Z0-9]+)", bloco)
    return m.group(1).lower() if m else ""


def _interno(bloco: str) -> str:
    """Conteúdo entre a tag de abertura e a de fechamento."""
    abertura = bloco.find(">")
    fechamento = bloco.rfind("</")
    if abertura == -1:
        return ""
    if fechamento <= abertura:
        return bloco[abertura + 1:].strip()
    return bloco[abertura + 1:fechamento].strip()


def _texto(bloco: str) -> str:
    """Texto visível, sem tags e com espaços normalizados."""
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", "", bloco))).strip()


def _tem_midia(bloco: str) -> bool:
    minusculo = bloco.lower()
    return "<img" in minusculo or "<figure" in minusculo or "<iframe" in minusculo


def _fecha_frase(bloco: str) -> bool:
    """True quando o bloco já termina uma frase e não deve ser colado ao seguinte."""
    texto = _texto(bloco)
    if not texto:
        return True
    if texto.endswith("..."):
        return True
    return texto.endswith(_TERMINA)


def _colar_texto(bloco: str, extra_html: str) -> str:
    """Acrescenta conteúdo ao fim do bloco, antes da tag de fechamento."""
    tag = _tag(bloco)
    fecha = bloco.rfind(f"</{tag}>")
    if fecha == -1:
        return f"{bloco} {extra_html}".strip()
    prefixo = bloco[:fecha].rstrip()
    return f"{prefixo} {extra_html.strip()}{bloco[fecha:]}"


def _itens(bloco_lista: str) -> list:
    return re.findall(r"<li\b[^>]*>.*?</li>", bloco_lista, flags=re.S | re.I)


def _absorver_em_lista(bloco_lista: str, extra_html: str) -> str:
    """Devolve a continuação para dentro do último `<li>` da lista."""
    ultimo = bloco_lista.rfind("</li>")
    if ultimo == -1:
        return bloco_lista
    return _colar_texto(bloco_lista[:ultimo], extra_html) + bloco_lista[ultimo:]


def reparar_paragrafos(markup: str, max_passadas: int = 6) -> str:
    """Devolve o HTML com a fragmentação de parágrafos e listas desfeita.

    Repete a passada porque uma junção pode criar a condição da seguinte: dois
    `<p>` colados viram um só e, com isso, o bloco passa a estar encaixado entre
    dois itens da mesma lista.
    """
    atual = markup
    for _ in range(max_passadas):
        novo = _uma_passada(atual)
        if novo == atual:
            break
        atual = novo
    return atual


def _uma_passada(markup: str) -> str:
    """Uma passada de junção de parágrafos e de listas do mesmo tipo."""
    blocos = [m.group(0) for m in _BLOCO.finditer(markup)]
    saida = []

    for indice, bloco in enumerate(blocos):
        tag = _tag(bloco)
        anterior = saida[-1] if saida else ""
        proximo = blocos[indice + 1] if indice + 1 < len(blocos) else ""

        if tag == "p" and not _tem_midia(bloco):
            if anterior and _tag(anterior) == "p" and not _fecha_frase(anterior):
                saida[-1] = _colar_texto(anterior, _interno(bloco))
                continue
            if anterior and _tag(anterior) == "p" and _texto(anterior).endswith(";") \
                    and _INICIA_MINUSCULA.match(_texto(bloco)):
                saida[-1] = _colar_texto(anterior, _interno(bloco))
                continue
            if anterior and _tag(anterior) in ("ol", "ul") and _tag(proximo) == _tag(anterior):
                # parágrafo encaixado entre dois itens da mesma lista
                saida[-1] = _absorver_em_lista(anterior, _interno(bloco))
                continue
            if anterior and _tag(anterior) in ("ol", "ul") \
                    and _INICIA_MINUSCULA.match(_texto(bloco)):
                ultimo = anterior.rfind("</li>")
                if ultimo != -1 and not _fecha_frase(anterior[:ultimo]):
                    saida[-1] = _absorver_em_lista(anterior, _interno(bloco))
                    continue
            saida.append(bloco)
            continue

        if tag in ("ol", "ul") and anterior and _tag(anterior) == tag:
            fecha = anterior.rfind(f"</{tag}>")
            if fecha != -1:
                saida[-1] = anterior[:fecha] + "".join(_itens(bloco)) + anterior[fecha:]
                continue

        saida.append(bloco)

    return "\n".join(saida)


def listas_seguidas(markup: str) -> int:
    """Quantas listas do mesmo tipo estão encostadas (sintoma de fragmentação)."""
    tipos = [_tag(m.group(0)) for m in _BLOCO.finditer(markup)]
    return sum(1 for a, b in zip(tipos, tipos[1:]) if a == b and a in ("ol", "ul"))
