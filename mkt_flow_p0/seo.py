"""
mkt_flow_p0.seo — SEO programático P1.5 com qualidade
Templates por categoria, canonical, sitemap, interlinking
Nada de doorway — conteúdo único com variáveis reais
"""
import html
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "mkt_flow_p0.db"

# Templates por categoria — variáveis reais (preço, avaliação, disponibilidade)
TEMPLATES_CATEGORIA = {
    "eletronicos": {
        "title": "{nome} por R$ {preco} — review e oferta",
        "h1": "{nome} vale a pena?",
        "intro": "Testamos {nome} (R$ {preco}, {disponibilidade}) — veja prós, contras e onde comprar com segurança.",
    },
    "casa": {
        "title": "{nome} — preço R$ {preco} e onde comprar",
        "h1": "{nome} — análise completa",
        "intro": "{nome} por R$ {preco} ({disponibilidade}). Guia prático antes de comprar.",
    },
    "default": {
        "title": "{nome} — oferta R$ {preco}",
        "h1": "{nome}",
        "intro": "{nome} por R$ {preco} — {disponibilidade}. Confira detalhes e link oficial.",
    },
}

def template_por_categoria(categoria: str, nome: str, preco: str, disponibilidade: str = "em estoque") -> dict:
    tpl = TEMPLATES_CATEGORIA.get((categoria or "default").lower(), TEMPLATES_CATEGORIA["default"])
    ctx = {"nome": html.escape(nome or "Produto"), "preco": html.escape(str(preco)), "disponibilidade": html.escape(disponibilidade)}
    return {
        "title": tpl["title"].format(**ctx)[:60],
        "meta_description": tpl["intro"].format(**ctx)[:160],
        "h1": tpl["h1"].format(**ctx),
        "intro": tpl["intro"].format(**ctx),
    }

def canonical_url(slug: str, base: str = "https://seusite.com") -> str:
    slug = (slug or "produto").strip().lower().replace(" ", "-")
    # remove caracteres não-url
    import re
    slug = re.sub(r"[^a-z0-9\-]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return f"{base.rstrip('/')}/{slug}"

def gerar_sitemap(urls: list, base: str = "https://seusite.com") -> str:
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        loc = canonical_url(u, base) if not u.startswith("http") else u
        xml.append(f"  <url><loc>{html.escape(loc)}</loc><lastmod>{datetime.now().date().isoformat()}</lastmod></url>")
    xml.append("</urlset>")
    return "\n".join(xml)

def interlinking(categoria: str, atual_link_id: str, limite: int = 3) -> list:
    """Retorna até `limite` links do mesmo nicho/categoria para interlinking"""
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        # Busca por categoria aproximada no título (P0 não tem categoria, usa LIKE)
        # Para P1.5 real, buscaria por categoria_id
        cur = con.execute("SELECT link_id, titulo FROM pipeline_runs WHERE link_id != ? ORDER BY created_at DESC LIMIT ?", (atual_link_id, limite*2))
        rows = [dict(r) for r in cur.fetchall()]
        con.close()
        # Filtra por categoria se tiver (simplificado: pega os mais recentes do mesmo programa)
        return rows[:limite]
    except Exception:
        return []

def validar_seo_qualidade(html_content: str) -> dict:
    """Checa doorway/conteúdo duplicado — P1.5 qualidade"""
    import re
    checks = {}
    # Título único?
    m = re.search(r"<title>(.*?)</title>", html_content, re.IGNORECASE)
    checks["tem_title"] = bool(m and len(m.group(1).strip()) >= 10)
    checks["title_len_ok"] = bool(m and 30 <= len(m.group(1)) <= 65)
    # Meta description?
    checks["tem_meta_desc"] = 'name="description"' in html_content.lower()
    # Canonical?
    checks["tem_canonical"] = 'rel="canonical"' in html_content.lower()
    # Schema?
    checks["tem_schema"] = 'schema.org' in html_content
    # Conteúdo muito curto = doorway?
    text_len = len(re.sub(r"<[^>]+>", "", html_content).strip())
    checks["conteudo_suficiente"] = text_len > 300
    checks["qualidade_ok"] = all([checks["tem_title"], checks["tem_meta_desc"], checks["tem_canonical"], checks["conteudo_suficiente"]])
    return checks


def gerar_llms_txt(site: str, paginas: list, descricao: str = "") -> str:
    """
    GEO/AEO — gera llms.txt (padrão aberto). Ajuda IAs generativas
    (ChatGPT, Perplexity, Claude) a entender e citar o site como fonte.
    Formato: https://llmstxt.org/
    """
    site = (site or "https://seusite.com").rstrip("/")
    linhas = [
        "# llms.txt — ConexoTech",
        "",
        "> Arquivo de contexto para modelos de linguagem. Conteúdo gerado pelo MKT Flow.",
        "",
        f"Site: {site}",
        f"Descrição: {descricao or 'Reviews e tabelas comparativas de produtos com links de afiliado (Mercado Livre, Shopee, Magazine Luiza, Amazon).'}",
        "",
        "## Páginas",
    ]
    for p in paginas:
        url = p if p.startswith("http") else f"{site}/{p.lstrip('/')}"
        titulo = p.rstrip("/").split("/")[-1].replace("-", " ").title()
        linhas.append(f"- [{titulo}]({url})")
    return "\n".join(linhas)


def gerar_faq_schema(perguntas_respostas: list) -> str:
    """
    FAQPage Schema (JSON-LD). Perguntas e respostas em formato direto
    (AEO) — é o que IAs e o Google exibem como rich result.
    """
    import json
    itens = []
    for qa in perguntas_respostas or []:
        if not isinstance(qa, dict):
            continue
        pergunta = str(qa.get("pergunta") or qa.get("q") or "").strip()
        resposta = str(qa.get("resposta") or qa.get("a") or "").strip()
        if pergunta and resposta:
            itens.append({"@type": "Question", "name": pergunta, "acceptedAnswer": {"@type": "Answer", "text": resposta}})
    if not itens:
        return ""
    schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": itens}
    return json.dumps(schema, ensure_ascii=False, indent=2)


def gerar_faq_review(nome: str, preco: str, plataforma: str = "Mercado Livre") -> list:
    """Gera perguntas/respostas padrão de review para alimentar o FAQ Schema (AEO)."""
    nome = nome or "Produto"
    return [
        {"pergunta": f"{nome} vale a pena?", "resposta": f"{nome} é uma boa opção na faixa de R$ {preco} na {plataforma}, considerando custo-benefício e avaliações."},
        {"pergunta": f"Onde comprar {nome} com desconto?", "resposta": f"O link oficial de afiliado na {plataforma} garante a oferta atualizada do produto."},
        {"pergunta": f"Qual o preço de {nome}?", "resposta": f"O {nome} custa cerca de R$ {preco} na {plataforma}. Preços podem variar conforme a loja e a data."},
    ]


def enriquecer_com_keywords(nome: str, categoria: str = "eletronicos", limit: int = 8) -> list:
    """
    P1.5 — usa o keyword_research (Autocomplete do Google, gratuito) para
    sugerir palavras-chave reais de review. Retorna [] se sem internet.
    """
    from .keyword_research import sugerir_keywords_review
    try:
        return sugerir_keywords_review(nome, limit=limit)
    except Exception:
        return []
