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


def contrato_seo_staging_wordpress(contrato):
    """Projeta contrato nativo consultivo para meta REST de staging do Conexo.

    Esta função não escreve WordPress, não assina contratos e não aprova conteúdo.
    Os campos de preview noindex/Schema continuam separados da entrega pública.
    """
    if not isinstance(contrato, dict) or contrato.get("schema_version") != "1.0":
        raise ValueError("Contrato SEO nativo invalido")
    if contrato.get("provider") != "native" or contrato.get("plugin_required") is not False:
        raise ValueError("Provedor SEO nativo obrigatorio")
    if contrato.get("delivery_status") != "not_written" or contrato.get("approved_for_publication") is not False:
        raise ValueError("Contrato consultivo nao pode estar aprovado")
    canonical = contrato.get("canonical")
    parsed = urlparse(canonical) if isinstance(canonical, str) else None
    if (not parsed or parsed.scheme != "https" or parsed.netloc != "conexotech.com.br"
            or not parsed.path.startswith("/") or not parsed.path.endswith("/")
            or parsed.query or parsed.fragment or parsed.username or parsed.password):
        raise ValueError("Canonical WP invalido")
    title, description = contrato.get("title"), contrato.get("description")
    if (not isinstance(title, str) or not title.strip() or len(title.encode("utf-8")) > 250
            or not isinstance(description, str) or not description.strip()
            or len(description.encode("utf-8")) > 600):
        raise ValueError("Texto SEO invalido para WordPress")
    return {
        "schema_version": "1.0",
        "provider": "native",
        "title": title.strip(),
        "description": description.strip(),
        "canonical": canonical,
        "delivery_status": "not_written",
        "approved_for_publication": False,
    }
