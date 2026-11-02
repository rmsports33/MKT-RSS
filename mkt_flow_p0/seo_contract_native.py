"""Contrato SEO consultivo, sem dependencia de plugins ou escrita WordPress."""
from urllib.parse import urlparse
import re

SITE_ORIGIN = "https://conexotech.com.br"

def contrato_seo_nativo(article, *, site_origin=SITE_ORIGIN):
    """Produz dados neutros para um adaptador do tema, nunca libera publicacao."""
    seo = article["seo"]
    slug = seo["slug"]
    origin = site_origin.rstrip("/")
    parsed = urlparse(origin)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.path or parsed.query or parsed.fragment
            or parsed.port not in (None, 443)):
        raise ValueError("Origem HTTPS do site invalida")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError("Slug SEO invalido")
    title = seo["title"].strip()
    description = seo["description"].strip()
    if not title or not description:
        raise ValueError("Titulo e descricao SEO obrigatorios")
    return {
        "schema_version": "1.0",
        "provider": "native",
        "plugin_required": False,
        "canonical": origin + "/" + slug + "/",
        "title": title,
        "description": description,
        "robots": "noindex,nofollow",
        "og": {"type": "article", "title": title, "description": description},
        "schema_type": "NewsArticle",
        "schema_status": "pending_editorial_review",
        "delivery_status": "not_written",
        "approved_for_publication": False,
    }
