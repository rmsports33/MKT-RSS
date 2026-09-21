#!/usr/bin/env python3
"""
pipeline_rss.py — Orquestrador RSS → WP draft (P0, independência de plugin)
Fluxo: feed → gate pauta (content_filter) → full-text (extractor) →
       reescrita (rewriter) → capa (image_handler) → rascunho WP → rss_runs.

Uso: python pipeline_rss.py [--limit 2] [--fonte tecnoblog] [--dry-run]
Env (.env) carregado dentro do main() — nunca no import.
"""
import argparse
import json
import logging
import os
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("pipeline_rss")

DB_PATH = Path(__file__).parent / "mkt_flow_p0.db"


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS rss_runs (
        id TEXT PRIMARY KEY, fonte TEXT, url TEXT, titulo_seo TEXT,
        palavras INTEGER, veredito TEXT, wp_post_id INTEGER, wp_link TEXT,
        custo_usd REAL DEFAULT 0, tokens_total INTEGER DEFAULT 0,
        created_at TEXT
    )""")
    # Migração suave se DB antigo não tem colunas novas
    try:
        con.execute("ALTER TABLE rss_runs ADD COLUMN custo_usd REAL DEFAULT 0")
    except Exception:
        pass
    try:
        con.execute("ALTER TABLE rss_runs ADD COLUMN tokens_total INTEGER DEFAULT 0")
    except Exception:
        pass
    con.commit()
    con.close()


def processar_item(item: dict, dry_run: bool = False) -> dict:
    """Processa 1 item RSS. Retorna {acao: publicado_rascunho|bloqueado|falha, ...}."""
    from mkt_flow_p0.content_filter import filtrar_item_rss, filtrar_conteudo, filtrar_por_tema
    from mkt_flow_p0.extractor import extrair_conteudo
    from mkt_flow_p0.rewriter import reescrever_materia, adicionar_atribuicao
    from mkt_flow_p0.image_handler import preparar_capa
    from mkt_flow_p0.format import markdown_para_html, sanitizar_url

    url_fonte = sanitizar_url(item.get("link", ""))
    # 1. Tema (whitelist tech) — antes de gastar rede/LLM
    tema = filtrar_por_tema(item.get("titulo", ""), item.get("resumo", ""))
    if tema["veredito"] == "BLOQUEADO":
        return {"acao": "bloqueado", "motivo": [tema["motivo"]], "termo": tema.get("termo",""), "url": url_fonte}

    gate = filtrar_item_rss({**item, "link": url_fonte})
    if gate["veredito"] == "BLOQUEADO":
        return {"acao": "bloqueado", "motivo": gate["categorias"], "url": url_fonte}

    ext = extrair_conteudo(url_fonte)
    if "erro" in ext:
        return {"acao": "falha", "motivo": ext["erro"], "url": url_fonte}
    if not ext.get("qualidade_ok"):
        return {"acao": "falha", "motivo": f"texto curto ({ext.get('palavras', 0)} palavras)", "url": url_fonte}

    # Revalida o corpo extraído (o excerpt do feed pode ser limpo e o corpo não)
    gate2 = filtrar_conteudo(ext.get("titulo", ""), (ext.get("texto") or "")[:4000])
    if gate2["veredito"] == "BLOQUEADO":
        return {"acao": "bloqueado", "motivo": gate2["categorias"], "url": url_fonte}

    if dry_run:
        return {"acao": "dry_run_ok", "palavras": ext["palavras"], "titulo": ext.get("titulo", "")}

    # Keywords reais (Autocomplete Google, grátis) — só após os gates passarem,
    # para não gastar autocomplete em item bloqueado. Falha aqui nunca trava a pauta.
    kws: list = []
    try:
        from mkt_flow_p0.seo import enriquecer_com_keywords
        kws = enriquecer_com_keywords(ext.get("titulo") or item.get("titulo", ""),
                                      categoria="", limit=8) or []
    except Exception as e:
        logger.warning(f"keywords puladas: {e}")

    rw = reescrever_materia(ext.get("titulo") or item.get("titulo", ""), ext["texto"],
                            fonte_nome=item.get("fonte", ""), url_fonte=url_fonte,
                            keywords=kws)
    if "erro" in rw:
        return {"acao": "falha", "motivo": rw["erro"], "url": url_fonte}

    texto_final = adicionar_atribuicao(rw["texto_markdown"], item.get("fonte", ""), url_fonte)
    html = markdown_para_html(texto_final)

    imagem_url, credito_foto = "", ""
    if ext.get("imagem"):
        capa = preparar_capa(sanitizar_url(ext["imagem"]), consulta_fallback=rw["titulo_seo"])
        if "bytes" in capa:
            imagem_url = sanitizar_url(ext["imagem"])  # WP baixa e define como destacada
            credito_foto = capa.get("credito", "")
        else:
            logger.warning(f"sem capa: {capa.get('erro')}")
    if credito_foto:
        html += f'\n<p class="credito-foto"><small>{credito_foto}</small></p>'

    wp_url = os.getenv("WP_URL", "")
    wp_result: dict = {"aviso": "WP_* não configurado — rascunho só local"}
    if wp_url and os.getenv("WP_USER", "") and os.getenv("WP_APP_PASSWORD", ""):
        from mkt_flow_p0.wp_publisher import publicar_no_wordpress, garantir_categoria, garantir_tag
        wp_user, wp_pwd = os.getenv("WP_USER", ""), os.getenv("WP_APP_PASSWORD", "")
        cat_id = garantir_categoria(wp_url, wp_user, wp_pwd, os.getenv("CATEGORIA_PADRAO", "Notícias"))
        tag_ids = [t for t in (garantir_tag(wp_url, wp_user, wp_pwd, t) for t in rw["tags"]) if t]
        try:
            from mkt_flow_p0.links_internos import sugerir, inserir_box
            _links = sugerir(html, ",".join(rw.get("tags", []) or []), wp_url)
            html = inserir_box(html, _links)
        except Exception as e:
            logger.warning(f"links internos pulados: {e}")
        wp_result = publicar_no_wordpress(
            rw["titulo_seo"], html, "PASS", wp_url, wp_user, wp_pwd,
            status_desejado="draft", imagem_url=imagem_url,
            categoria_ids=[cat_id] if cat_id else None,
            tag_ids=tag_ids or None,
            slug=rw["slug"],
            rank_math={"title": rw["titulo_seo"], "description": rw["meta_description"],
                       "focus": (rw["tags"] or [""])[0]},
        )

    run_id = str(uuid.uuid4())[:8]
    init_db()
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT INTO rss_runs (id, fonte, url, titulo_seo, palavras, veredito, wp_post_id, wp_link, custo_usd, tokens_total, created_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (run_id, item.get("fonte", ""), item.get("link", ""), rw["titulo_seo"], rw["palavras"],
                 gate2["veredito"], (wp_result or {}).get("post_id"), (wp_result or {}).get("link"),
                 float(rw.get("custo_usd_estimado", 0) or 0), int((rw.get("uso_tokens") or {}).get("total", 0) or 0),
                 datetime.now().isoformat()))
    con.commit()
    con.close()
    return {"acao": "publicado_rascunho", "run_id": run_id, "titulo_seo": rw["titulo_seo"],
            "palavras": rw["palavras"], "custo_usd": rw.get("custo_usd_estimado", 0),
            "tokens": (rw.get("uso_tokens") or {}).get("total", 0), "wp": wp_result}


def publicar_indice() -> dict:
    """Sitemap editorial: página WP 'mapa-do-site' + arquivos sitemap.xml/llms.txt.

    Chamado no fim do run (sem WP configurado, só gera arquivos locais).
    """
    from mkt_flow_p0.seo import gerar_sitemap, gerar_llms_txt
    from mkt_flow_p0.wp_publisher import publicar_pagina

    init_db()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        cur = con.execute("SELECT titulo_seo, wp_link FROM rss_runs WHERE wp_link IS NOT NULL "
                          "ORDER BY created_at DESC LIMIT 100")
        links = [(r["titulo_seo"] or "Post", r["wp_link"]) for r in cur.fetchall()]
    except Exception:
        links = []
    finally:
        con.close()
    if not links:
        return {"aviso": "sem links publicados ainda — índice na próxima"}
    base = os.getenv("WP_URL", "https://conexotech.com.br").rstrip("/")
    Path("./sitemap.xml").write_text(gerar_sitemap([u for _, u in links], base), encoding="utf-8")
    Path("./llms.txt").write_text(
        gerar_llms_txt(base, [u for _, u in links], "Notícias tech reescritas do ConexoTech."), encoding="utf-8")
    itens = "\n".join(f"<li><a href='{u}'>{t}</a></li>" for t, u in links)
    html = f"<h2>Últimas notícias publicadas</h2>\n<ul>\n{itens}\n</ul>"
    if not (os.getenv("WP_URL", "") and os.getenv("WP_USER", "") and os.getenv("WP_APP_PASSWORD", "")):
        return {"arquivos": ["sitemap.xml", "llms.txt"], "aviso": "WP ausente — suba llms.txt na raiz via hospedagem"}
    r = publicar_pagina("Mapa do Site — Automático", html, "mapa-do-site",
                        os.getenv("WP_URL", ""), os.getenv("WP_USER", ""), os.getenv("WP_APP_PASSWORD", ""))
    r["arquivos"] = ["sitemap.xml", "llms.txt"]
    return r


def main():
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent / ".env")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Pipeline RSS → rascunho WP")
    ap.add_argument("--limit", type=int, default=2)
    ap.add_argument("--fonte", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    from mkt_flow_p0.rss_ingestor import FEEDS_PADRAO, buscar_novidades
    alvos = {k: v for k, v in FEEDS_PADRAO.items() if not args.fonte or k == args.fonte}
    if args.fonte and args.fonte not in FEEDS_PADRAO:
        print(json.dumps({"erro": f"fonte desconhecida: {args.fonte}. Opções: {sorted(FEEDS_PADRAO)}"}))
        sys.exit(2)
    total = {"publicado_rascunho": 0, "bloqueado": 0, "falha": 0, "dry_run_ok": 0}
    for fonte, url in alvos.items():
        # dry-run nunca marca como visto (não gasta a pauta do dia)
        nov = buscar_novidades(url, fonte=fonte, limit=args.limit, marcar=not args.dry_run)
        if "erro" in nov:
            print(json.dumps({"fonte": fonte, "erro": nov["erro"]}, ensure_ascii=False))
            continue
        for item in nov.get("novos", []):
            r = processar_item(item, dry_run=args.dry_run)
            total[r["acao"]] = total.get(r["acao"], 0) + 1
            print(json.dumps({"fonte": fonte, **r}, ensure_ascii=False))
    if not args.dry_run and total.get("publicado_rascunho"):
        try:
            print(json.dumps({"indice": publicar_indice()}, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"indice_erro": str(e)[:150]}, ensure_ascii=False))
    print(json.dumps({"resumo": total}, ensure_ascii=False))


if __name__ == "__main__":
    main()
