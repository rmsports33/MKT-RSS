"""Diagnostico de prontidao ConexoTech, sem aprovar fatos ou publicacao.

Rascunho privado pode existir com pendencias. Somente a revisao humana,
com aceite da versao, determina autorizacao para publicar.
"""
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

from mkt_flow_p0.editorial_identity import validar_handoff_chatgpt

SITE = "conexotech.com.br"
LIMITES_POR_GENERO = {"noticia": 550, "guia": 700, "comparativo": 800,
                      "analise": 750, "review": 800, "nota_breve": 180}


class _LinksInternos(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paths = set()
        self.headings = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h2":
            self.headings += 1
        if tag != "a":
            return
        raw = a.get("href")
        if not isinstance(raw, str):
            return
        try:
            parsed = urlsplit(raw)
        except ValueError:
            return
        if parsed.scheme == "https" and parsed.hostname == SITE and parsed.path not in ("", "/"):
            self.paths.add(parsed.path.rstrip("/"))
        elif not parsed.scheme and not parsed.netloc and raw.startswith("/") and parsed.path not in ("", "/"):
            self.paths.add(parsed.path.rstrip("/"))


def avaliar_prontidao_editorial(handoff, *, html="", genero="noticia",
                                featured_media_id=None, direitos_imagem_confirmados=False):
    """Checklist verificavel, sem inferir evidencias nem criar referencias falsas."""
    try:
        validar_handoff_chatgpt(handoff)
    except (ValueError, TypeError):
        return {"status": "PACOTE_INVALIDO", "pendencias": ["handoff_invalido"],
                "pronto_para_publicar": False}
    meta = handoff["metadata"]
    markdown = handoff["markdown"]
    palavras = len(re.findall(r"\b[\wÀ-ÿ]+\b", markdown, re.UNICODE))
    genero = genero if genero in LIMITES_POR_GENERO else "noticia"
    limite = LIMITES_POR_GENERO[genero]
    links = _LinksInternos()
    links.feed(html if isinstance(html, str) else "")
    fontes = meta["sources"]
    seo = meta.get("seo", {})
    desc = seo.get("description", "") if isinstance(seo, dict) else ""
    pendencias = []
    if palavras < limite:
        pendencias.append("texto_abaixo_da_referencia_do_genero")
    if genero != "nota_breve" and len(fontes) < 2:
        pendencias.append("pesquisa_multifonte_pendente")
    if links.headings < 2 and genero != "nota_breve":
        pendencias.append("desenvolvimento_em_secoes_pendente")
    if len(links.paths) < 3 and genero != "nota_breve":
        pendencias.append("tres_links_internos_pendentes")
    if (type(featured_media_id) is not int or featured_media_id <= 0
            or direitos_imagem_confirmados is not True):
        pendencias.append("imagem_destacada_com_direitos_pendente")
    if not isinstance(desc, str) or not 100 <= len(desc.strip()) <= 170:
        pendencias.append("descricao_seo_revisar")
    return {
        "status": "PRONTO_PARA_REVISAO_HUMANA" if not pendencias else "ENRIQUECIMENTO_PENDENTE",
        "pendencias": pendencias,
        "genero": genero, "palavras": palavras, "referencia_palavras": limite,
        "fontes": len(fontes), "links_internos": len(links.paths),
        "subtitulos_h2": links.headings,
        "imagem_destacada_confirmada": "imagem_destacada_com_direitos_pendente" not in pendencias,
        "revisao_factual": "PENDENTE",
        "pronto_para_publicar": False,
    }
