"""
mkt_flow_p0.landing — Gerador de landing pages HTML (P0 unificado).
Escape de HTML em todos os campos externos (XSS) + gate PASS para CTA.
API rica como o módulo clássico: gerar_landing_page_completa() -> dict.

Pré-processamento externo: HTML pronto antes do LLM; modelo só comenta.
"""
import html
import logging
import os
import re

logger = logging.getLogger("landing")


def slugify(texto: str) -> str:
    s = (texto or "").strip().lower()
    s = re.sub(r"[^a-z0-9\s\-]+", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "produto"


def _ga_script() -> str:
    """Bloco Google Analytics 4 (gtag) se GA_MEASUREMENT_ID estiver no env, senão vazio."""
    gaid = os.getenv("GA_MEASUREMENT_ID", "").strip()
    if not gaid:
        return ""
    return f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={html.escape(gaid)}"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', '{html.escape(gaid)}');
document.addEventListener('click', function(e){{
  var a = e.target.closest && e.target.closest('a[data-ga="affiliate_click"]');
  if (a) {{ gtag('event', 'affiliate_click', {{'event_category': 'afiliado'}}); }}
}});
</script>"""


def gerar_template_landing_page(nome_produto: str, link_afiliado: str, preco: str,
                                descricao: str = "", status_validacao: str = "PASS",
                                imagem_url: str = "") -> str:
    """Gera HTML da landing. CTA só existe com status_validacao==PASS.

    FAIL/UNKNOWN → página BLOQUEADA sem link de saída (gate de compliance).
    Todos os campos externos escapados contra XSS.
    """
    if (status_validacao or "PASS") != "PASS":
        logger.warning(f"landing bloqueada: status_validacao={status_validacao}")
        return (
            "<!DOCTYPE html><html lang=\"pt-BR\"><head><meta charset=\"UTF-8\">"
            "<title>Oferta bloqueada</title></head><body>"
            f"<p><strong>BLOQUEADO</strong> — status_validacao={html.escape(str(status_validacao))}. "
            "Só PASS permite divulgação. Verifique tag de rastreamento e policy.</p>"
            "</body></html>"
        )

    nome_seguro = html.escape(nome_produto or "Oferta")
    preco_seguro = html.escape(str(preco or ""))
    link_seguro = html.escape(link_afiliado or "#", quote=True)
    desc_seguro = html.escape(descricao or f"Oferta de {nome_produto or 'produto'}")
    img_seguro = html.escape(imagem_url or "", quote=True)
    slug = slugify(nome_produto)
    meta_desc = (desc_seguro[:200]) if len(desc_seguro) > 200 else desc_seguro
    ga = _ga_script()

    img_tag = f'<img src="{img_seguro}" alt="{nome_seguro}" style="max-width:100%;border-radius:8px;" loading="lazy">' if img_seguro else ""
    schema = (
        '{"@context": "https://schema.org", "@type": "Product", '
        f'"name": "{nome_seguro}", "description": "{desc_seguro[:200]}"'
        + (f', "image": "{img_seguro}"' if img_seguro else "")
        + (f', "offers": {{"@type": "Offer", "price": "{preco_seguro}", "priceCurrency": "BRL"}}' if preco_seguro else "")
        + "}"
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Oferta - {nome_seguro}</title>
    <meta name="description" content="{meta_desc}">
    <meta property="og:title" content="{nome_seguro}">
    <meta property="og:description" content="{meta_desc}">
    <link rel="canonical" href="https://conexotech.com.br/{slug}">
    <script type="application/ld+json">{schema}</script>
    {ga}
    <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; background: #f8f9fa; display: flex; justify-content: center; padding: 20px; margin: 0; }}
        .card {{ background: #fff; max-width: 420px; width: 100%; padding: 24px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); text-align: center; box-sizing: border-box; }}
        .price {{ font-size: 1.5rem; color: #2e7d32; font-weight: bold; margin: 12px 0; }}
        .btn {{ display: block; background: #1976d2; color: white; padding: 12px; border-radius: 6px; text-decoration: none; font-weight: 600; margin-top: 16px; }}
        .legal {{ font-size: 0.75rem; color: #6c757d; margin-top: 16px; }}
    </style>
</head>
<body>
    <div class="card">
        {img_tag}
        <h1>{nome_seguro}</h1>
        <p>{desc_seguro}</p>
        <div class="price">R$ {preco_seguro}</div>
        <a href="{link_seguro}" class="btn" target="_blank" rel="noopener sponsored" data-ga="affiliate_click">Ir para a Loja Oficial</a>
        <p class="legal">Comprando pelo link acima, podemos receber uma comissão sem custo adicional para você. #ad #linkdeafiliado</p>
    </div>
</body>
</html>"""


def gerar_landing_page_completa(nome_produto: str, link_afiliado: str, preco: str,
                                descricao: str = "", status_validacao: str = "PASS",
                                imagem_url: str = "", base_url: str = "https://conexotech.com.br") -> dict:
    """Versão rica: retorna dict com html/slug/url_amigavel/meta (unificação v3.11)."""
    slug = slugify(nome_produto)
    html_pag = gerar_template_landing_page(nome_produto, link_afiliado, preco, descricao, status_validacao, imagem_url)
    return {
        "html": html_pag,
        "slug": slug,
        "url_amigavel": f"{base_url.rstrip('/')}/{slug}",
        "meta": {
            "title": f"Oferta - {nome_produto or 'Produto'}"[:60],
            "description": (descricao or f"Oferta de {nome_produto or 'produto'}")[:160],
        },
        "status_validacao": status_validacao,
    }
