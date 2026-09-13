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

    # 1. Tema (whitelist tech) — antes de gastar rede/LLM
    tema = filtrar_por_tema(item.get("titulo", ""), item.get("resumo", ""))
    if tema["veredito"] == "BLOQUEADO":
        return {"acao": "bloqueado", "motivo": [tema["motivo"]], "termo": tema.get("termo",""), "url": item.get("link", "")}

    gate = filtrar_item_rss(item)
    if gate["veredito"] == "BLOQUEADO":
        return {"acao": "bloqueado", "motivo": gate["categorias"], "url": item.get("link", "")}

    ext = extrair_conteudo(item.get("link", ""))
    if "erro" in ext:
        return {"acao": "falha", "motivo": ext["erro"], "url": item.get("link", "")}
    if not ext.get("qualidade_ok"):
        return {"acao": "falha", "motivo": f"texto curto ({ext.get('palavras', 0)} palavras)", "url": item.get("link", "")}

    # Revalida o corpo extraído (o excerpt do feed pode ser limpo e o corpo não)
    gate2 = filtrar_conteudo(ext.get("titulo", ""), (ext.get("texto") or "")[:4000])
    if gate2["veredito"] == "BLOQUEADO":
        return {"acao": "bloqueado", "motivo": gate2["categorias"], "url": item.get("link", "")}

    if dry_run:
        return {"acao": "dry_run_ok", "palavras": ext["palavras"], "titulo": ext.get("titulo", "")}

    rw = reescrever_materia(ext.get("titulo") or item.get("titulo", ""), ext["texto"],
                            fonte_nome=item.get("fonte", ""), url_fonte=item.get("link", ""))
    if "erro" in rw:
        return {"acao": "falha", "motivo": rw["erro"], "url": item.get("link", "")}

    texto_final = adicionar_atribuicao(rw["texto_markdown"], item.get("fonte", ""), item.get("link", ""))
    html = (f"<h1>{rw['titulo_seo']}</h1>\n"
            f"<!-- meta: {rw['meta_description']} | tags: {', '.join(rw['tags'])} -->\n"
            + "\n".join(f"<p>{p.strip('# ').strip()}</p>" if not p.startswith("#") else f"<h2>{p.strip('# ').strip()}</h2>"
                        for p in texto_final.split("\n\n") if p.strip()))

    imagem_url = ""
    if ext.get("imagem"):
        capa = preparar_capa(ext["imagem"], consulta_fallback=rw["titulo_seo"])
        if "bytes" in capa:
            imagem_url = ext["imagem"]  # WP baixa e define como destacada
        else:
            logger.warning(f"sem capa: {capa.get('erro')}")

    wp_url = os.getenv("WP_URL", "")
    wp_result: dict = {"aviso": "WP_* não configurado — rascunho só local"}
    if wp_url and os.getenv("WP_USER", "") and os.getenv("WP_APP_PASSWORD", ""):
        from mkt_flow_p0.wp_publisher import publicar_no_wordpress
        wp_result = publicar_no_wordpress(rw["titulo_seo"], html, "PASS", wp_url,
                                          os.getenv("WP_USER", ""), os.getenv("WP_APP_PASSWORD", ""),
                                          status_desejado="draft", imagem_url=imagem_url)

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
        nov = buscar_novidades(url, fonte=fonte, limit=args.limit)
        if "erro" in nov:
            print(json.dumps({"fonte": fonte, "erro": nov["erro"]}, ensure_ascii=False))
            continue
        for item in nov.get("novos", []):
            r = processar_item(item, dry_run=args.dry_run)
            total[r["acao"]] = total.get(r["acao"], 0) + 1
            print(json.dumps({"fonte": fonte, **r}, ensure_ascii=False))
    print(json.dumps({"resumo": total}, ensure_ascii=False))


if __name__ == "__main__":
    main()
