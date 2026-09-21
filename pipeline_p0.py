#!/usr/bin/env python3
"""
pipeline_p0.py — Orquestrador P0 ponta a ponta
Uso: python pipeline_p0.py "https://mercadolivre.com/sec/MLB123?matt_word=xxx" [--publish] [--cpc 0.5 --cliques 1000 --conversao 2.0 --comissao 10]
"""
import argparse
import json
import logging
import re
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path

from mkt_flow_p0.validator import validar_link_afiliado
from mkt_flow_p0.api_ml import consultar_api_publica_mercado_livre
from mkt_flow_p0.policy_engine import avaliar_politica, construir_contexto_politica_llm
from mkt_flow_p0.roi import calcular_roi_afiliado
from mkt_flow_p0.landing import gerar_template_landing_page
from mkt_flow_p0.link_tracker import registrar_publicacao, init_link_tables
from mkt_flow_p0.seo import gerar_sitemap, validar_seo_qualidade, canonical_url, gerar_llms_txt, gerar_faq_schema, gerar_faq_review, enriquecer_com_keywords

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("pipeline_p0")

DB_PATH = Path(__file__).parent / "mkt_flow_p0.db"

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS pipeline_runs (
        id TEXT PRIMARY KEY, link TEXT, link_id TEXT, status_validacao TEXT, status_politica TEXT,
        titulo TEXT, preco REAL, roi_json TEXT, wp_post_id INTEGER, wp_link TEXT, created_at TEXT
    )""")
    con.commit()
    con.close()

def extrair_item_id(url: str) -> str:
    m = re.search(r"(MLB\d+)", url, re.IGNORECASE)
    return m.group(1).upper() if m else ""

def main():
    # .env carregado aqui (não no import): evita poluir os.environ de quem
    # importa este módulo (ex.: suíte de testes) — refactor 12/09/2026.
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent / ".env")
        load_dotenv(Path(__file__).parent / "MKTFLOW" / ".env", override=False)
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Pipeline P0 MKT Flow — ML afiliado → WP draft")
    parser.add_argument("link", help="Link de afiliado (Mercado Livre com matt_word/matt_tool/tag)")
    parser.add_argument("--publish", action="store_true", help="Tenta publicar como publish (só se PASS). Default é draft")
    parser.add_argument("--cpc", type=float, default=0.5)
    parser.add_argument("--cliques", type=int, default=1000)
    parser.add_argument("--conversao", type=float, default=2.0)
    parser.add_argument("--comissao", type=float, default=8.0, help="%% comissão (se não souber, use 0 e ROI ficará UNKNOWN)")
    parser.add_argument("--deducao", type=float, default=0.0)
    args = parser.parse_args()

    link_id = str(uuid.uuid4())[:8]
    print(f"[{link_id}] Iniciando pipeline P0 para: {args.link}")

# 1. Validar link
    v = validar_link_afiliado(args.link, timeout=5, resolver_redirect=True)
    print(json.dumps({"etapa": "validacao", "link_id": link_id, **v}, ensure_ascii=False, indent=2))
    if v["status_validacao"] != "PASS":
        print(f"[{link_id}] BLOQUEADO na validação: {v['status']} — verifique tag de rastreamento e domínio.")
        if v["status_validacao"] == "UNKNOWN":
            print(f"[{link_id}] O que falta verificar: confirme manualmente se o link contém tag válida e aponta para um anúncio específico de produto no portal do afiliado.")
        sys.exit(2)
    # Regra ML-GENERIC-DESTINATION: destino precisa ser produto
    if v.get("destino") not in (None, "produto"):
        print(f"[{link_id}] BLOQUEADO: destino do link = '{v.get('destino')}' — a regra ML-GENERIC-DESTINATION (cl. 3.1.2(d)) exige link para anúncio específico. Gere um Link Especial de produto no portal do afiliado.")
        sys.exit(2)

    # 2. Buscar dados ML
    item_id = extrair_item_id(v.get("url_final") or args.link)
    dados_ml = {}
    if item_id:
        dados_ml = consultar_api_publica_mercado_livre(item_id)
        print(json.dumps({"etapa": "api_ml", "item_id": item_id, **dados_ml}, ensure_ascii=False, indent=2))
        if "erro" in dados_ml:
            print(f"[{link_id}] Aviso API ML: {dados_ml['erro']} — segue com dados do link apenas (ROI ficará limitado).")
            dados_ml = {}
    else:
        print(json.dumps({"etapa": "api_ml", "aviso": "item_id não encontrado na URL, ROI sem preço real"}, ensure_ascii=False))

    # 3. Policy Engine
    programa = "mercado_livre" if v["plataforma"] == "Mercado Livre" else "shopee"
    fatos = {
        "midia_cadastrada": True,
        "destino_produto_especifico": True,
        "cookie_clique_visivel": True,
        "usa_shortener": False,
        "compara_com_outro_produto": False,
        "simula_canal_oficial": False,
        "midia_paga": False,
        "informacoes_constam_anuncio": True,
    }
    pol = avaliar_politica(programa, fatos)
    print(json.dumps({"etapa": "policy", **pol}, ensure_ascii=False, indent=2))
    ctx_llm = construir_contexto_politica_llm(pol)
    print(json.dumps({"etapa": "policy_context_llm", **ctx_llm}, ensure_ascii=False, indent=2))
    if pol["status_politica"] == "FAIL":
        print(f"[{link_id}] BLOQUEADO por Policy Engine: {pol['regras'][0]['evidencia'] if pol['regras'] else 'FAIL'}")
        sys.exit(3)
    if pol["status_politica"] == "UNKNOWN":
        print(f"[{link_id}] BLOQUEADO: Policy UNKNOWN — não gerar divulgação. Verifique: {[r['regra_id'] for r in pol['regras']]}")
        sys.exit(3)

    # 4. ROI
    preco = dados_ml.get("preco")
    roi = None
    if preco and args.comissao:
        roi = calcular_roi_afiliado(args.cpc, args.cliques, args.conversao, float(preco), args.comissao, args.deducao)
        print(json.dumps({"etapa": "roi", **roi}, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"etapa": "roi", "aviso": "ROI UNKNOWN — preço ou comissão ausente. Informe --comissao com valor da categoria."}, ensure_ascii=False))

    # 5. Gerar landing
    titulo = dados_ml.get("titulo") or "Oferta Especial"
    preco_str = str(dados_ml.get("preco") or "")
    desc = f"Oferta de {titulo}" if titulo else ""
    imagem = (dados_ml.get("imagens") or [""])[0] if dados_ml.get("imagens") else ""
    html = gerar_template_landing_page(titulo, v.get("url_final") or args.link, preco_str, desc, status_validacao=v["status_validacao"], imagem_url=imagem)
    if "BLOQUEADO" in html:
        print(f"[{link_id}] Landing bloqueada por gate PASS.")
        sys.exit(4)
    # P1.5 SEO validação
    seo_check = validar_seo_qualidade(html)
    print(json.dumps({"etapa": "seo_check", **seo_check}, ensure_ascii=False, indent=2))
    if not seo_check["qualidade_ok"]:
        print(f"[{link_id}] Aviso SEO: qualidade_ok=False — verifique title/meta/canonical/conteúdo")
    # P1.5 GEO/AEO — keywords sugeridas (Autocomplete gratuito) + FAQ schema + llms.txt
    try:
        kws = enriquecer_com_keywords(titulo, categoria="eletronicos", limit=8)
        print(json.dumps({"etapa": "keywords_sugeridas", "quantidade": len(kws), "keywords": kws}, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[{link_id}] Aviso keywords: {e}")
    try:
        faq = gerar_faq_review(titulo, preco_str or "—")
        faq_schema = gerar_faq_schema(faq)
        if faq_schema:
            with open(f"./faq_{link_id}.json", "w", encoding="utf-8") as f:
                f.write(faq_schema)
            print(f"[{link_id}] FAQ Schema gerado: ./faq_{link_id}.json (cole no Rank Math ou no post)")
    except Exception as e:
        print(f"[{link_id}] Aviso faq: {e}")
    try:
        llms = gerar_llms_txt("https://conexotech.com.br", [f"oferta/{titulo.lower().replace(' ', '-')}"], f"Oferta de {titulo}")
        Path("./llms.txt").write_text(llms, encoding="utf-8")
        print(f"[{link_id}] GEO: llms.txt gerado em ./llms.txt")
    except Exception as e:
        print(f"[{link_id}] Aviso llms.txt: {e}")
    out_html = Path(f"./landing_{link_id}.html")
    out_html.write_text(html, encoding="utf-8")
    print(f"[{link_id}] Landing gerada: {out_html.resolve()}")

    # 6. Publicar WP (draft por padrão)
    wp_url = __import__("os").getenv("WP_URL", "")
    wp_user = __import__("os").getenv("WP_USER", "")
    wp_pwd = __import__("os").getenv("WP_APP_PASSWORD", "")
    wp_result = {"aviso": "WP_* não configurado — pulei publicação. Configure .env para publicar."}
    if wp_url and wp_user and wp_pwd:
        from mkt_flow_p0.wp_publisher import publicar_no_wordpress
        status_desejado = "publish" if args.publish else "draft"
        wp_result = publicar_no_wordpress(titulo, html, v["status_validacao"], wp_url, wp_user, wp_pwd, status_desejado=status_desejado, imagem_url=imagem)
        print(json.dumps({"etapa": "wp", **wp_result}, ensure_ascii=False, indent=2))
        if "erro" in wp_result and "bloqueada" in wp_result["erro"].lower():
            sys.exit(5)
    else:
        print(json.dumps({"etapa": "wp", **wp_result}, ensure_ascii=False))

    # 7. Histórico + P1.1 rastreabilidade
    init_db()
    init_link_tables()
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT INTO pipeline_runs (id, link, link_id, status_validacao, status_politica, titulo, preco, roi_json, wp_post_id, wp_link, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (link_id, args.link, link_id, v["status_validacao"], pol["status_politica"], titulo, preco, json.dumps(roi) if roi else None, wp_result.get("post_id"), wp_result.get("link"), datetime.now().isoformat()))
    con.commit()
    con.close()
    # P1.1 — registra onde foi publicado
    try:
        if wp_result.get("link"):
            registrar_publicacao(link_id, args.link, "wordpress", programa, wp_result["link"], v["status_validacao"])
        # sempre registra o arquivo estático local
        registrar_publicacao(link_id, args.link, "site_estatico", programa, str(out_html.resolve()), v["status_validacao"])
        print(f"[{link_id}] Rastreio P1.1 registrado (link_id={link_id})")
    except Exception as e:
        print(f"[{link_id}] Aviso rastreio: {e}")
    # P2.1 — sitemap automático + interlinking
    try:
        import sqlite3 as _sql
        con2 = _sql.connect(DB_PATH)
        con2.row_factory = _sql.Row
        cur = con2.execute("SELECT url_publicacao FROM link_publicacoes WHERE url_publicacao LIKE 'http%' ORDER BY created_at DESC LIMIT 100")
        urls = [r[0] for r in cur.fetchall()]
        # adiciona a landing atual se for http (quando WP publicou) ou mantém file:// fora do sitemap
        urls_http = [u for u in urls if u.startswith("http")]
        if urls_http:
            sitemap_xml = gerar_sitemap(urls_http)
            Path("./sitemap.xml").write_text(sitemap_xml, encoding="utf-8")
            print(json.dumps({"etapa": "sitemap", "urls": len(urls_http), "arquivo": str(Path("./sitemap.xml").resolve())}, ensure_ascii=False, indent=2))
        con2.close()
    except Exception as e:
        print(f"[{link_id}] Aviso sitemap: {e}")
    print(f"[{link_id}] Histórico registrado em {DB_PATH}")
    print(f"[{link_id}] PIPELINE P0+P1.1+P2.1 CONCLUÍDO — draft gerado com PASS. Link ID: {link_id}")

if __name__ == "__main__":
    main()

