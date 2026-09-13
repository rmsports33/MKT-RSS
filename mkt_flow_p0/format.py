"""
mkt_flow_p0.format — Formatação de saída (P0).
Corrige 3 defeitos vistos em produção (12/09/2026, posts ?p=9127/9129/9131):
1. `**negrito**` e listas vazando literais (conversor antigo só tratava `#`).
2. Título cortado no meio da palavra ("Fabricantes opi").
3. URLs com controles/soft-hyphen (`￾`) quebrando link de fonte.
Puro (sem rede/LLM) e 100% testável offline.
"""
import html
import re
import unicodedata


def sanitizar_url(url: str) -> str:
    """Remove controles, soft-hyphen (U+00AD) e espaços da URL.
    NOTA: os literais invisíveis abaixo são U+00AD de propósito (ver teste)."""
    SOFT = chr(0xAD)  # soft-hyphen: invisível, quebra URLs copiadas de portais
    u = "".join(c for c in (url or "") if unicodedata.category(c) != "Cc" and c != SOFT)
    return u.replace(SOFT, "").strip()
    SOFT = chr(0xAD)  # soft-hyphen: invisível, quebra URLs copiadas de portais
    u = "".join(c for c in (url or "") if unicodedata.category(c) != "Cc" and c != SOFT)
    return u.replace(SOFT, "").strip()


def truncar_palavras(texto: str, limite: int) -> str:
    """Corta em fronteira de palavra (nunca no meio). Sem corte se couber."""
    t = (texto or "").strip()
    if len(t) <= limite:
        return t
    corte = t[:limite].rsplit(" ", 1)
    base = corte[0] if len(corte) > 1 and corte[0] else t[:limite]
    return base.rstrip(" ,;:.-")


def _inline(texto: str) -> str:
    """Negrito/itálico/code inline com escape primeiro (anti-XSS)."""
    t = html.escape(texto)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    # Links Markdown [texto](url) com URL sanitizada
    def _link(m):
        return f'<a href="{html.escape(sanitizar_url(m.group(2)), quote=True)}" target="_blank" rel="noopener">{m.group(1)}</a>'
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link, t)


def markdown_para_html(markdown: str) -> str:
    """Converte subconjunto Markdown (H2/H3, listas ol/ul, hr, parágrafos)."""
    blocos, lista = [], None  # lista: None | "ol" | "ul"
    def _fecha():
        nonlocal lista
        if lista:
            blocos.append(f"</{lista}>")
            lista = None

    for raw in (markdown or "").split("\n"):
        linha = raw.strip()
        if not linha:
            _fecha()
            continue
        if set(linha) == {"-"} or linha == "---":
            _fecha()
            blocos.append("<hr>")
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", linha)
        if m:
            _fecha()
            nivel = 2 if len(m.group(1)) <= 2 else 3  # # e ## viram h2 (h1 é o título do post)
            blocos.append(f"<h{nivel}>{_inline(m.group(2))}</h{nivel}>")
            continue
        m = re.match(r"^\d+[.)]\s+(.*)$", linha)
        if m:
            if lista != "ol":
                _fecha()
                blocos.append("<ol>")
                lista = "ol"
            blocos.append(f"<li>{_inline(m.group(1))}</li>")
            continue
        m = re.match(r"^[-*•]\s+(.*)$", linha)
        if m:
            if lista != "ul":
                _fecha()
                blocos.append("<ul>")
                lista = "ul"
            blocos.append(f"<li>{_inline(m.group(1))}</li>")
            continue
        _fecha()
        blocos.append(f"<p>{_inline(linha)}</p>")
    _fecha()
    return "\n".join(blocos)
