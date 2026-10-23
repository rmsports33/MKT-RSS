#!/usr/bin/env python3
"""
pipeline_rss.py — Orquestrador RSS → WP draft (P0, independência de plugin)
Fluxo: feed → gate pauta (content_filter) → full-text (extractor) →
       gate valor opt-in (M04.16D) → reescrita (rewriter) → capa
       (image_handler) → rascunho WP → rss_runs.

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


def classificar_resultado_wp(resultado: dict) -> str:
    """Only a confirmed WordPress draft counts as successful delivery."""
    if (isinstance(resultado, dict) and not resultado.get("erro")
            and resultado.get("post_id") and resultado.get("status") == "draft"):
        return "publicado_rascunho"
    return "falha"


# M04.16D — gate de valor no pipeline. Ativação explícita e desligada por
# padrão: sem GATE_PUBLICACAO_ENABLED o fluxo é idêntico ao anterior.
_GATE_PUBLICACAO_ENV = "GATE_PUBLICACAO_ENABLED"
_VALORES_LIGADOS = frozenset({"1", "true", "yes", "on"})


def gate_publicacao_ativo() -> bool:
    """True só com ativação explícita; qualquer outro valor mantém o gate off."""
    return os.getenv(_GATE_PUBLICACAO_ENV, "").strip().lower() in _VALORES_LIGADOS


def avaliar_gate_publicacao(titulo: str, texto: str, links: list) -> dict:
    """Roda gate_publicacao sobre o conteúdo extraído, fail-closed.

    Erro na validação vira BLOQUEADO: o pipeline nunca segue para a IA sem a
    prova de que o gate avaliou o conteúdo com sucesso.
    """
    from mkt_flow_p0.content_filter import gate_publicacao
    try:
        return gate_publicacao(titulo=titulo, texto=texto, links=links)
    except Exception as e:
        logger.warning(f"gate_publicacao falhou (fail-closed): {e}")
        return {
            "veredito": "BLOQUEADO",
            "criterios": [],
            "motivo": "erro_validacao_gate",
            "aviso": f"gate_publicacao não pôde avaliar o conteúdo: {e}",
        }


def processar_item(item: dict, dry_run: bool = False, evidencias_aprovadas: dict = None, capturas_aprovadas: dict = None) -> dict:
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

    # M04.16D: gate de valor opt-in, após a extração e antes da IA. Recebe o
    # título/texto extraídos e a URL da fonte como única evidência conhecida.
    if gate_publicacao_ativo():
        gate_valor = avaliar_gate_publicacao(
            ext.get("titulo") or item.get("titulo", ""),
            ext.get("texto") or "",
            [url_fonte] if url_fonte else [],
        )
        # Fail-closed: apenas APROVADO prossegue. Qualquer outro veredito
        # (REVISAR, BLOQUEADO, ou ausência de chave) interrompe o fluxo.
        if gate_valor.get("veredito") != "APROVADO":
            logger.info(f"gate_publicacao bloqueou {url_fonte}: {gate_valor.get('motivo') or gate_valor.get('veredito')}")
            return {
                "acao": "bloqueado",
                "motivo": gate_valor.get("motivo") or gate_valor.get("veredito") or "sem_valor_acrescentado",
                "criterios": gate_valor.get("criterios", []),
                "aviso": gate_valor.get("aviso", ""),
                "url": url_fonte,
            }

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
                            keywords=kws, evidencias_aprovadas=evidencias_aprovadas)
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

    # C19: nunca considerar a ausencia de alertas como aprovacao factual.
    # A integracao do contrato de evidencias permanece obrigatoria.
    from mkt_flow_p0.gate_editorial_pos_ia import validar_saida
    try:
        auditoria_pos_ia = validar_saida(ext["texto"], rw["texto_markdown"])
    except Exception as exc:
        logger.warning("Gate editorial pos-IA falhou: %s", exc)
        auditoria_pos_ia = {"veredito": "BLOQUEADO", "motivos": ["erro_gate_pos_ia"]}
    # SEM_ALERTAS significa somente ausencia dos alertas implementados.
    # Nao ha atestado independente de cada claim: manter envio WP bloqueado.
    # Se o produtor fornecer snapshot v1.0, avaliar sua rastreabilidade.
    # A ausencia do snapshot e uma falha, nunca uma aprovacao implicita.
    from mkt_flow_p0.adaptador_contrato_editorial import avaliar_snapshot_editorial
    try:
        auditoria_evidencias = avaliar_snapshot_editorial(rw.get("contrato_editorial"))
    except Exception as exc:
        logger.warning("Contrato editorial invalido: %s", exc)
        auditoria_evidencias = {"veredito": "BLOQUEADO", "motivos": ["erro_contrato_editorial"]}
    from mkt_flow_p0.lastro_offline_noticia import auditar_lastro_offline
    auditoria_lastro = auditar_lastro_offline(rw.get("contrato_editorial"), capturas_aprovadas)
    # Mesmo EVIDENCIAS_ESTRUTURADAS nao certifica as claims do HTML.
    verificacao_factual = "NAO_VERIFICADO"
    # M05.2C: uma unica saida fail-closed, independente de credenciais WP.
    # Nenhum estado de evidencias atual autoriza publicacao ou draft remoto.
    return {
        "acao": "bloqueado",
        "motivo": "gate_factual_pos_ia_nao_integrado",
        "url": url_fonte,
        "escreveu": False,
        "custo_usd": float(rw.get("custo_usd_estimado", 0) or 0),
        "tokens": int((rw.get("uso_tokens") or {}).get("total", 0) or 0),
        "auditoria_pos_ia": auditoria_pos_ia,
        "auditoria_evidencias": auditoria_evidencias,
        "auditoria_lastro": auditoria_lastro,
        "verificacao_factual": verificacao_factual,
        "aviso": "HTML gerado localmente; envio ao WordPress bloqueado ate certificacao factual.",
    }


def publicar_indice() -> dict:
    """Public sitemap is disabled for the draft-only RSS pipeline."""
    return {"aviso": "indice publico desativado: RSS produz apenas rascunhos"}


def main():
    try:
        from dotenv import load_dotenv
        central = Path.home() / ".conexotech.env"
        if central.exists():
            load_dotenv(central, override=False)
        load_dotenv(Path(__file__).parent / ".env", override=False)
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
    from mkt_flow_p0.rss_ingestor import marcar_visto
    for fonte, url in alvos.items():
        # dry-run nunca marca como visto (não gasta a pauta do dia)
        nov = buscar_novidades(url, fonte=fonte, limit=args.limit, marcar=False)
        if "erro" in nov:
            print(json.dumps({"fonte": fonte, "erro": nov["erro"]}, ensure_ascii=False))
            continue
        for item in nov.get("novos", []):
            r = processar_item(item, dry_run=args.dry_run)
            if r["acao"] == "publicado_rascunho" and not args.dry_run:
                marcar_visto(fonte, item["link"], item["titulo"])
            total[r["acao"]] = total.get(r["acao"], 0) + 1
            print(json.dumps({"fonte": fonte, **r}, ensure_ascii=False))
    print(json.dumps({"resumo": total}, ensure_ascii=False))


if __name__ == "__main__":
    main()
