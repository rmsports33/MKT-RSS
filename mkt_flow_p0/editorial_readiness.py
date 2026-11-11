"""Diagnostico de prontidao ConexoTech, sem aprovar fatos ou publicacao.

Rascunho privado pode existir com pendencias. Somente a revisao humana,
com aceite da versao, determina autorizacao para publicar.
"""
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

from mkt_flow_p0.editorial_identity import validar_handoff_chatgpt, verificar_aplicacao_voz

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


def _publisher_domain(url):
    """Conservative grouping: multiple URLs of one outlet are not multifonte."""
    if not isinstance(url, str):
        return None
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower().rstrip(".").removeprefix("www.")
        if parsed.scheme != "https" or not host or parsed.username or parsed.password:
            return None
        labels = host.split(".")
        if len(labels) < 2:
            return None
        suffix2 = ".".join(labels[-2:])
        common_second_level_suffixes = {
            "com.br", "net.br", "org.br", "gov.br", "edu.br",
            "co.uk", "org.uk", "ac.uk", "com.au", "org.au",
            "com.mx", "com.ar", "co.jp", "co.kr", "co.nz",
        }
        if suffix2 in common_second_level_suffixes and len(labels) >= 3:
            return ".".join(labels[-3:])
        return suffix2
    except ValueError:
        return None


def avaliar_prontidao_editorial(handoff, *, html="", genero="noticia",
                                featured_media_id=None, direitos_imagem_confirmados=False,
                                verified_related_urls=None):
    """Checklist verificavel, sem inferir evidencias nem criar referencias falsas."""
    try:
        validar_handoff_chatgpt(handoff)
    except (ValueError, TypeError):
        return {"status": "PACOTE_INVALIDO", "pendencias": ["handoff_invalido"],
                "pronto_para_publicar": False}
    meta = handoff["metadata"]
    voice_application = verificar_aplicacao_voz(meta)
    markdown = handoff["markdown"]
    palavras = len(re.findall(r"\b[\wÀ-ÿ]+\b", markdown, re.UNICODE))
    genero = genero if genero in LIMITES_POR_GENERO else "noticia"
    limite = LIMITES_POR_GENERO[genero]
    links = _LinksInternos()
    links.feed(html if isinstance(html, str) else "")
    # URLs in the article are untrusted until confirmed from published WP posts.
    # Merely pointing to the correct domain does not prove an article exists.
    trusted = set()
    if isinstance(verified_related_urls, (list, tuple, set)):
        for url in verified_related_urls:
            if not isinstance(url, str):
                continue
            try:
                parsed = urlsplit(url)
                if (parsed.scheme == "https" and parsed.hostname == SITE
                        and not parsed.username and not parsed.password
                        and not parsed.query and not parsed.fragment
                        and parsed.path not in ("", "/")):
                    trusted.add(parsed.path.rstrip("/"))
            except ValueError:
                continue
    linked_verified = links.paths & trusted
    fontes = meta["sources"]
    # RSS excerpts are discovery hints, NOT independent factual corroboration.
    # The user must review the source before it can satisfy editorial readiness.
    fontes_rss_pendentes = sum(
        1 for s in fontes if isinstance(s, dict)
        and isinstance(s.get("name"), str)
        and "(RSS pendente de apuração)" in s["name"])
    seo = meta.get("seo", {})
    desc = seo.get("description", "") if isinstance(seo, dict) else ""
    from mkt_flow_p0.editorial_substance import assess_substance
    substance = assess_substance(markdown, meta.get("editorial_brief"),
                                 meta.get("editorial_substance_review"))
    pendencias = list(substance["pendencias"])
    # A real MDA A/B draft contained a 3-column table with 2-cell data rows.
    # Structural errors remain editorial pendências; never confer publication rights.
    from mkt_flow_p0.editorial_voice_adapter import markdown_table_structure_signals
    pendencias.extend(markdown_table_structure_signals(markdown)["signals"])
    if isinstance(meta.get("editorial_brief"), dict) and meta["editorial_brief"].get("genre", genero) != genero:
        pendencias.append("briefing_genero_divergente")
    avisos = ["texto_abaixo_da_referencia_do_genero"] if palavras < limite else []
    if voice_application["status"] not in {"PROMPT_APPLIED", "HUMAN_ADAPTED", "ASSISTED_ADAPTED"}:
        pendencias.append("persona_editorial_nao_aplicada")
    # Two URLs from Apple or another publisher remain one editorial source.
    # Domain diversity is a conservative discovery heuristic, not factual approval.
    dominios_distintos = {
        _publisher_domain(source.get("url"))
        for source in fontes
        if isinstance(source, dict)
        and isinstance(source.get("name"), str)
        and "(RSS pendente de apuração)" not in source["name"]
    }
    dominios_distintos.discard(None)
    if genero != "nota_breve" and len(dominios_distintos) < 2:
        pendencias.append("pesquisa_multifonte_pendente")
    if fontes_rss_pendentes:
        pendencias.append("fontes_rss_candidatas_sem_verificacao")
    if links.headings < 2 and genero != "nota_breve":
        pendencias.append("desenvolvimento_em_secoes_pendente")
    # DNA vigente: até três links genuinamente relacionados, sem quota artificial.
    if links.paths - trusted:
        pendencias.append("links_internos_nao_verificados")
    if len(links.paths) > 3:
        pendencias.append("mais_de_tres_links_internos")
    if not links.paths:
        avisos.append("sem_links_internos_relacionados")
    if (type(featured_media_id) is not int or featured_media_id <= 0
            or direitos_imagem_confirmados is not True):
        pendencias.append("imagem_destacada_com_direitos_pendente")
    if not isinstance(desc, str) or not 100 <= len(desc.strip()) <= 170:
        pendencias.append("descricao_seo_revisar")
    return {
        "status": "PRONTO_PARA_REVISAO_HUMANA" if not pendencias else "ENRIQUECIMENTO_PENDENTE",
        "pendencias": pendencias, "avisos": avisos,
        "persona_editorial": voice_application,
        "revisao_de_voz": "PENDENTE_AVALIACAO_HUMANA",
        "avaliacao_substantiva": substance,
        "genero": genero, "palavras": palavras, "referencia_palavras": limite,
        "fontes": len(fontes), "fontes_rss_pendentes": fontes_rss_pendentes,
        "dominios_editoriais_distintos_identificados": len(dominios_distintos),
        "links_internos": len(links.paths),
        "links_internos_verificados": len(linked_verified),
        "subtitulos_h2": links.headings,
        "imagem_destacada_confirmada": "imagem_destacada_com_direitos_pendente" not in pendencias,
        "revisao_factual": "PENDENTE",
        "pronto_para_publicar": False,
    }
