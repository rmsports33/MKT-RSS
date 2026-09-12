"""MKTFLOW.seo_programmatic — SEO programático clássico (v3.11 congelado)."""
import logging
from datetime import date

logger = logging.getLogger("mktflow.seo")


def generate_programmatic_pages(produtos: list, template: str = "{nome} — oferta") -> list:
    """Gera páginas a partir de dados reais (anti-doorway: pula item sem nome/preço)."""
    paginas = []
    for p in produtos or []:
        nome = (p or {}).get("nome", "").strip()
        preco = (p or {}).get("preco", "")
        if not nome or preco in ("", None):
            continue
        titulo = template.replace("{nome}", nome).replace("{preco}", str(preco))
        slug = "".join(c.lower() if c.isalnum() else "-" for c in titulo)[:70].strip("-")
        paginas.append({"titulo": titulo, "slug": slug or "produto",
                        "conteudo": f"{titulo}. Preço R$ {preco}. Confira detalhes e link oficial."})
    return paginas


def build_sitemap(urls: list, base: str = "https://seusite.com") -> str:
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls or []:
        loc = u if str(u).startswith("http") else base.rstrip("/") + "/" + str(u).lstrip("/")
        xml.append(f"  <url><loc>{loc}</loc><lastmod>{date.today().isoformat()}</lastmod></url>")
    xml.append("</urlset>")
    return "\n".join(xml)


def get_seo_stats(paginas: list) -> dict:
    total = len(paginas or [])
    com_titulo = sum(1 for p in (paginas or []) if len((p or {}).get("titulo", "")) >= 10)
    return {"total_paginas": total, "com_titulo_ok": com_titulo,
            "cobertura": round(com_titulo / total * 100, 1) if total else 0.0}
