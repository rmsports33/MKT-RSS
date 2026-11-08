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


def confirmar_readback_trilha(resultado: dict) -> bool:
    """A telemetry PASS requires the actual successful draft readback result."""
    return (
        isinstance(resultado, dict)
        and resultado.get("acao") == "publicado_rascunho"
        and resultado.get("status") == "draft"
        and type(resultado.get("post_id")) is int
        and resultado["post_id"] > 0
        and not resultado.get("erro")
    )


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


def processar_pacote_editorial(package, *, core_root, actor_id, intent="stage", publication_reference=None, operation_nonce=None, trace_run_id=None):
    """Conclusão supervisionada da pauta RSS; jamais certifica texto automaticamente."""
    from mkt_flow_p0.editorial_transport import publish_package
    payload = package.get("payload", {}) if isinstance(package, dict) else {}
    discovery = payload.get("discovery")
    if (not isinstance(discovery, dict) or not isinstance(discovery.get("pauta_id"), str)
            or len(discovery["pauta_id"]) != 32
            or any(c not in "0123456789abcdef" for c in discovery["pauta_id"])
            or not any(isinstance(s, dict) and s.get("url") == discovery.get("source_url")
                       for s in payload.get("sources", []))):
        return {"acao": "bloqueado", "erro": "origem da pauta RSS não corresponde às fontes apuradas"}
    return publish_package(package, core_root=core_root, actor_id=actor_id, intent=intent, operation_nonce=operation_nonce,
        trace_run_id=trace_run_id, publication_reference=publication_reference, wp_url=os.getenv("WP_URL", ""),
        wp_user=os.getenv("WP_USER", ""), wp_password=os.getenv("WP_APP_PASSWORD", ""))


def processar_item(item: dict, dry_run: bool = False, evidencias_aprovadas: dict = None, capturas_aprovadas: dict = None,
                   pacote_editorial=None, core_root=None, actor_id=None, contexto_complementar=None, handoff_only=False,
                   featured_media_id=None, media_rights_confirmed=False) -> dict:
    """Processa RSS: rascunho WP, handoff offline ou bloqueio sem publicar."""
    if pacote_editorial is not None:
        if handoff_only:
            return {"acao": "bloqueado", "erro": "handoff-only não aceita pacote de publicação"}
        discovery = pacote_editorial.get("payload", {}).get("discovery", {})
        if dry_run or discovery.get("source_url") != item.get("link"):
            return {"acao": "bloqueado", "erro": "dry-run não escreve; pauta deve corresponder ao pacote"}
        return processar_pacote_editorial(pacote_editorial, core_root=core_root, actor_id=actor_id)
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

    contexto_pesquisa = contexto_complementar
    if contexto_pesquisa is None and os.getenv("CONEXO_RSS_RESEARCH_FEEDS") == "1":
        from mkt_flow_p0.research_candidates import descobrir_fontes_candidatas
        try:
            contexto_pesquisa = descobrir_fontes_candidatas(
                ext.get("titulo") or item.get("titulo", ""), url_fonte,
                fonte_original=item.get("fonte", ""))
        except (ValueError, TypeError, OSError) as exc:
            logger.warning("Pesquisa RSS auxiliar indisponivel: %s", str(exc)[:100])
            contexto_pesquisa = None
    rw = reescrever_materia(ext.get("titulo") or item.get("titulo", ""), ext["texto"],
                            fonte_nome=item.get("fonte", ""), url_fonte=url_fonte,
                            keywords=kws, evidencias_aprovadas=evidencias_aprovadas,
                            contexto_complementar=contexto_pesquisa)
    if "erro" in rw:
        from mkt_flow_p0.editorial_trace import make_trace
        trace = make_trace(url_fonte, "", error=rw["erro"])
        return {"acao": "falha", "motivo": rw["erro"], "url": url_fonte,
                "editorial_trace": trace}

    texto_final = adicionar_atribuicao(rw["texto_markdown"], item.get("fonte", ""), url_fonte)
    relacionados = []
    if os.getenv("CONEXO_RSS_RELATED_LINKS") == "1":
        from mkt_flow_p0.related_posts import buscar_relacionados_wordpress, anexar_relacionados
        relacionados = buscar_relacionados_wordpress(
            rw["titulo_seo"], "https://conexotech.com.br")
        if relacionados:
            texto_final = anexar_relacionados(texto_final, relacionados)
    # O pacote deve representar exatamente o Markdown convertido em HTML.
    # Se o handoff anterior era invalido, NAO regenerar um hash para conserta-lo.
    if isinstance(rw.get("editorial_handoff"), dict):
        from mkt_flow_p0.editorial_identity import atualizar_handoff_revisao
        try:
            rw["editorial_handoff"] = atualizar_handoff_revisao(
                rw["editorial_handoff"], texto_final, related_articles=relacionados,
                featured_media_id=featured_media_id,
                media_rights_confirmed=media_rights_confirmed)
        except ValueError:
            pass  # O validador do fluxo bloqueia o handoff antigo ou invalido.
    html = markdown_para_html(texto_final)

    # Imagens externas e extraídas do RSS não são autorizadas automaticamente.
    # A pesquisa gratuita é opt-in, sem upload nem escrita WordPress.
    plano_imagem = {"status": "PESQUISA_NAO_EXECUTADA",
                    "proxima_etapa": "BUSCAR_BANCO_GRATUITO"}
    if not handoff_only and os.getenv("CONEXO_RSS_PREVIEW_SOURCE_IMAGE") == "1":
        plano_imagem = preparar_capa(consulta_fallback=rw["titulo_seo"], timeout=10)
    # Qualquer candidata permanece pendente de licença/atribuição e de
    # revisão 1440px desktop / 390px celular. Não altera hash do artigo.
    # Diagnostico de prontidao nao bloqueia o armazenamento de rascunhos;
    # sinaliza lacunas antes da revisao humana e NUNCA autoriza publicacao.
    from mkt_flow_p0.editorial_readiness import avaliar_prontidao_editorial
    qualidade_editorial = avaliar_prontidao_editorial(
        rw.get("editorial_handoff"), html=html,
        genero=item.get("genero", "noticia"),
        featured_media_id=featured_media_id,
        direitos_imagem_confirmados=media_rights_confirmed,
        verified_related_urls=[x["url"] for x in relacionados])

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
    from mkt_flow_p0.auditoria_cobertura_pos_ia import auditar_cobertura_pos_ia
    try:
        auditoria_cobertura = auditar_cobertura_pos_ia(
            rw["texto_markdown"], rw.get("contrato_editorial"), capturas_aprovadas,
            referencias_traducao=rw.get("referencias_traducao"))
    except Exception as exc:
        logger.warning("Auditoria de cobertura pos-IA falhou: %s", exc)
        auditoria_cobertura = {"veredito": "BLOQUEADO", "motivos": ["erro_auditoria_cobertura"]}
    # Nenhuma análise automática certifica fatos: a publicação continua
    # condicionada à revisão humana. Porém o WordPress nativo pode receber
    # rascunhos privados para edição sem depender do novo Editorial Gate.
    verificacao_factual = "NAO_VERIFICADO"
    # Build provenance from the observed Groq response, not from an
    # imagined editorial approval. Full output gets its own content hash.
    from mkt_flow_p0.editorial_trace import make_trace
    trace = make_trace(url_fonte, texto_final, generated=rw,
                       readiness=qualidade_editorial)
    if handoff_only:
        handoff = rw.get("editorial_handoff")
        if not isinstance(handoff, dict):
            return {"acao": "falha", "motivo": "handoff_editorial_ausente",
                    "url": url_fonte, "escreveu": False}
        from mkt_flow_p0.editorial_identity import validar_handoff_chatgpt
        try:
            validar_handoff_chatgpt(handoff)
        except ValueError:
            return {"acao": "falha", "motivo": "handoff_editorial_invalido",
                    "url": url_fonte, "escreveu": False}
        return {
            "acao": "pacote_editorial_criado", "escreveu": False,
            "qualidade_editorial": qualidade_editorial,
            "editorial_handoff": handoff, "url": url_fonte,
            "editorial_trace": trace,
            "verificacao_factual": verificacao_factual,
            "auditoria_pos_ia": auditoria_pos_ia,
            "auditoria_evidencias": auditoria_evidencias,
            "auditoria_lastro": auditoria_lastro,
            "auditoria_cobertura": auditoria_cobertura,
        }
    if os.environ.get("CONEXO_RSS_DRAFT") == "1" or os.environ.get("CONEXO_RSS_DRAFT_STAGING") == "1":
        # Drafts must carry the same verified, still-unapproved editorial
        # handoff as the no-write pipeline. No silent bypass on missing data.
        handoff = rw.get("editorial_handoff")
        if not isinstance(handoff, dict):
            return {"acao": "falha", "motivo": "handoff_editorial_ausente",
                    "url": url_fonte, "escreveu": False}
        from mkt_flow_p0.editorial_identity import validar_handoff_chatgpt
        try:
            validar_handoff_chatgpt(handoff)
        except ValueError:
            return {"acao": "falha", "motivo": "handoff_editorial_invalido",
                    "url": url_fonte, "escreveu": False}
        from mkt_flow_p0.wp_draft_staging import stage_rss_draft
        staged = stage_rss_draft(
            title=rw["titulo_seo"], content=html, source_url=url_fonte,
            wp_url=os.environ.get("WP_URL", ""), wp_user=os.environ.get("WP_USER", ""),
            wp_password=os.environ.get("WP_APP_PASSWORD", ""),
            featured_media_id=featured_media_id,
            media_rights_confirmed=media_rights_confirmed,
        )
        staged_trace = make_trace(
            url_fonte, texto_final, generated=rw, readiness=qualidade_editorial,
            post_id=staged.get("post_id") if type(staged.get("post_id")) is int else None,
            wp_readback=confirmar_readback_trilha(staged))
        return {**staged,
                "editorial_trace": staged_trace,
                "qualidade_editorial": qualidade_editorial,
                "editorial_handoff": rw.get("editorial_handoff"),
                "url": url_fonte,
                "verificacao_factual": verificacao_factual,
                "auditoria_pos_ia": auditoria_pos_ia,
                "auditoria_evidencias": auditoria_evidencias,
                "auditoria_lastro": auditoria_lastro,
                "auditoria_cobertura": auditoria_cobertura}
    # Compatibilidade: modo desligado mantém a recusa anterior e não escreve.
    return {
        "acao": "bloqueado",
        "motivo": "gate_factual_pos_ia_nao_integrado",
        "qualidade_editorial": qualidade_editorial,
        "editorial_trace": trace,
        "editorial_handoff": rw.get("editorial_handoff"),
        "url": url_fonte,
        "escreveu": False,
        "custo_usd": float(rw.get("custo_usd_estimado", 0) or 0),
        "tokens": int((rw.get("uso_tokens") or {}).get("total", 0) or 0),
        "auditoria_pos_ia": auditoria_pos_ia,
        "auditoria_evidencias": auditoria_evidencias,
        "auditoria_lastro": auditoria_lastro,
        "auditoria_cobertura": auditoria_cobertura,
        "verificacao_factual": verificacao_factual,
        "plano_imagem": plano_imagem,
        "aviso": "HTML gerado localmente; envio ao WordPress bloqueado ate certificacao factual.",
    }


def autorizar_transicao_publicacao(post_persistido: dict, revisao_factual: dict = None, *, pacote_editorial=None, core_root=None) -> dict:
    """Guard shared by any future WordPress publisher; no remote write.

    The caller must supply a freshly read WordPress post and independently
    certified editorial evidence. Never infer approval from RSS queue status.
    """
    from editorial_publish_gate import authorize_publish
    return authorize_publish(post_persistido, revisao_factual, package=pacote_editorial, core_root=core_root)


def inspecionar_rascunho_wordpress(fetch_post, post_id: int, revisao_factual: dict) -> dict:
    """Read-only persisted draft check; never writes or publishes."""
    from editorial_wordpress_adapter import inspect_wordpress_draft
    return inspect_wordpress_draft(fetch_post, post_id, revisao_factual)

def planejar_transicao_publicacao(post_persistido: dict, revisao_factual: dict) -> dict:
    """Return an offline plan only; never publish directly from RSS."""
    from editorial_publish_transition import plan_publish_transition
    return plan_publish_transition(post_persistido, revisao_factual)

def publicar_indice() -> dict:
    """Public sitemap is disabled for the draft-only RSS pipeline."""
    return {"aviso": "indice publico desativado: RSS produz apenas rascunhos"}



def resumo_seguro_cli(fonte: str, resultado: dict) -> dict:
    """Emit only operational metadata: never unpublished body, claims or evidence.

    This is particularly important for public GitHub Actions logs, which may be
    readable by third parties even when the underlying draft remains private.
    The complete handoff is stored on disk under --handoff-dir.
    """
    if not isinstance(resultado, dict):
        return {"fonte": fonte, "acao": "falha", "motivo": "resultado_invalido"}
    output = {"fonte": fonte, "acao": resultado.get("acao", "desconhecido")}
    simple = ("post_id", "status", "palavras", "escreveu",
              "verificacao_factual", "handoff_path", "trace_path",
              "central_trace_synced", "turso_trace_synced")
    for key in simple:
        value = resultado.get(key)
        if isinstance(value, (str, int, float, bool)) and not isinstance(value, complex):
            output[key] = value if not isinstance(value, str) else value[:160]
    reason = resultado.get("motivo", resultado.get("erro"))
    if isinstance(reason, str):
        # Do not print provider error bodies or HTTP secrets verbatim.
        allowed = ("GROQ_API_KEY ausente", "handoff_editorial_ausente",
                   "handoff_editorial_invalido", "erro_persistencia_handoff")
        output["motivo"] = next((x for x in allowed if reason.startswith(x)), "falha_processamento")
    elif isinstance(reason, list):
        output["motivo"] = "revisao_necessaria"
    quality = resultado.get("qualidade_editorial")
    if isinstance(quality, dict):
        output["quality_status"] = quality.get("status")
        output["quality_pending"] = quality.get("pendencias", [])[:12]
        output["quality_words"] = quality.get("palavras")
    # Identifiers only: never log unpublished content or credentials.
    trace = resultado.get("editorial_trace")
    if isinstance(trace, dict):
        run_id = trace.get("run_id")
        if isinstance(run_id, str) and len(run_id) <= 128:
            output["trace_run_id"] = run_id
        output["trace_statuses"] = {
            event["stage"]: event["status"]
            for event in trace.get("events", [])[:12]
            if isinstance(event, dict)
            and isinstance(event.get("stage"), str)
            and isinstance(event.get("status"), str)
        }
    handoff = resultado.get("editorial_handoff")
    if isinstance(handoff, dict):
        v = handoff.get("version_sha256")
        if isinstance(v, str) and len(v) == 64:
            output["handoff_sha256"] = v
        output["review_status"] = handoff.get("review_status") == "PENDING_HUMAN_REVIEW"
        m = handoff.get("metadata")
        if isinstance(m, dict):
            output["sources_count"] = len(m.get("sources", [])) if isinstance(m.get("sources"), list) else 0
            output["claims_count"] = len(m.get("claims", [])) if isinstance(m.get("claims"), list) else 0
    return output


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
    ap.add_argument("--queue-only", action="store_true", help="Coletar apenas pautas na fila, sem IA ou WordPress")
    ap.add_argument("--research-context", type=Path,
                    help="JSON com source_url + sources complementares para UMA pauta correspondente")
    ap.add_argument("--handoff-dir", type=Path,
                    help="Salvar pacote editorial versionado em diretório local")
    ap.add_argument("--featured-media-id", type=int,
                    help="ID de imagem ja presente no WP, autorizada explicitamente")
    ap.add_argument("--confirm-media-rights", action="store_true",
                    help="O operador confirmou os direitos de reutilizacao desta imagem")
    ap.add_argument("--handoff-only", action="store_true",
                    help="Gerar apenas pacote para revisão; nunca escrever no WordPress")
    ap.add_argument("--editorial-package", type=Path, help="Pacote canônico já apurado/revisado; sem geração automática")
    ap.add_argument("--core-root", type=Path)
    ap.add_argument("--trace-db", type=Path,
                    help="SQLite do traço central; exige --core-root com biblioteca Conexo OS")
    ap.add_argument("--trace-turso", action="store_true",
                    help="Persistir traço no Turso existente, somente host explicitamente autorizado")
    ap.add_argument("--actor-id", type=int)
    ap.add_argument("--intent", choices=("stage", "draft", "publish", "schedule"), default="stage")
    ap.add_argument("--publication-reference", help="Referência real da ordem específica de publicar/agendar")
    ap.add_argument("--operation-nonce", help="Retoma somente consulta da operação anterior; nunca repete escrita")
    ap.add_argument("--trace-run-id", help="Execução no Turso homologada para preflight de publicação assinada")
    args = ap.parse_args()
    if args.trace_db and not args.core_root:
        ap.error("--trace-db requer --core-root; sem ele só o sidecar é gravado")
    if args.handoff_only:
        if (args.editorial_package or args.queue_only or args.dry_run
                or args.handoff_dir is None):
            ap.error("--handoff-only exige --handoff-dir e não combina com --editorial-package, --queue-only ou --dry-run")
        if not args.fonte or args.limit != 1:
            ap.error("--handoff-only requer --fonte NOME --limit 1 para limitar chamadas à IA")
    if args.featured_media_id is not None or args.confirm_media_rights:
        if (args.featured_media_id is None or args.featured_media_id <= 0
                or not args.confirm_media_rights or not args.fonte or args.limit != 1
                or args.queue_only or args.handoff_only or args.dry_run
                or args.editorial_package):
            ap.error("--featured-media-id exige --confirm-media-rights, --fonte, --limit 1 e modo rascunho")
    contexto_pesquisa = None
    if args.research_context:
        if args.editorial_package:
            ap.error("--research-context exige fluxo RSS, não --editorial-package")
        if args.queue_only:
            ap.error("--research-context não combina com --queue-only")
        try:
            if args.research_context.stat().st_size > 512 * 1024:
                raise ValueError("pesquisa complementar excede 512 KiB")
            loaded = json.loads(args.research_context.read_text(encoding="utf-8"))
            if (not isinstance(loaded, dict) or set(loaded) != {"source_url", "sources"}
                    or not isinstance(loaded["source_url"], str)):
                raise ValueError("formato exige source_url e sources")
            from mkt_flow_p0.editorial_identity import normalizar_fontes_complementares
            normalizar_fontes_complementares({"sources": loaded["sources"]})
            contexto_pesquisa = loaded
        except (OSError, ValueError, TypeError) as exc:
            ap.error("pesquisa complementar inválida: " + str(exc))
    if args.editorial_package:
        if args.dry_run or args.queue_only or not args.core_root or not args.actor_id:
            ap.error("pacote exige core-root/actor-id e não combina com dry-run/queue-only")
        try:
            package = json.loads(args.editorial_package.read_text(encoding="utf-8"))
            result = processar_pacote_editorial(package, core_root=args.core_root, actor_id=args.actor_id,
                intent=args.intent, publication_reference=args.publication_reference, operation_nonce=args.operation_nonce,
                trace_run_id=args.trace_run_id)
        except (ValueError, OSError, TypeError) as exc:
            result = {"erro": "pacote inválido", "reason": str(exc)}
        print(json.dumps(result, ensure_ascii=False))
        return 1 if result.get("erro") else 0
    if args.queue_only:
        if args.dry_run:
            ap.error("--queue-only e --dry-run são mutuamente exclusivos")
        if not 1 <= args.limit <= 50:
            ap.error("--limit deve estar entre 1 e 50 no modo fila")
        from rss_queue_collect import coletar
        try:
            resultado = coletar(fonte=args.fonte, limite=args.limit)
        except (ValueError, RuntimeError, OSError) as exc:
            print(json.dumps({"erro": str(exc)}, ensure_ascii=False))
            sys.exit(1)
        print(json.dumps(resultado, ensure_ascii=False))
        if resultado.get("falhas"):
            sys.exit(1)
        return

    from mkt_flow_p0.rss_ingestor import FEEDS_PADRAO, buscar_novidades
    alvos = {k: v for k, v in FEEDS_PADRAO.items() if not args.fonte or k == args.fonte}
    if args.fonte and args.fonte not in FEEDS_PADRAO:
        print(json.dumps({"erro": f"fonte desconhecida: {args.fonte}. Opções: {sorted(FEEDS_PADRAO)}"}))
        sys.exit(2)
    total = {"publicado_rascunho": 0, "pacote_editorial_criado": 0, "bloqueado": 0, "falha": 0, "feed_error": 0, "dry_run_ok": 0}
    contexto_usado = False
    from mkt_flow_p0.rss_ingestor import marcar_visto
    for fonte, url in alvos.items():
        # dry-run nunca marca como visto (não gasta a pauta do dia)
        nov = buscar_novidades(url, fonte=fonte, limit=args.limit, marcar=False)
        if "erro" in nov:
            total["feed_error"] += 1
            print(json.dumps({"fonte": fonte, "erro": nov["erro"], "acao": "falha_feed"}, ensure_ascii=False))
            continue
        for item in nov.get("novos", []):
            enriquecimento = ({"sources": contexto_pesquisa["sources"]}
                              if contexto_pesquisa is not None
                              and item.get("link") == contexto_pesquisa["source_url"]
                              else None)
            if enriquecimento is not None:
                contexto_usado = True
            r = processar_item(item, dry_run=args.dry_run,
                               contexto_complementar=enriquecimento,
                               handoff_only=args.handoff_only,
                               featured_media_id=args.featured_media_id,
                               media_rights_confirmed=args.confirm_media_rights)
            if args.handoff_dir and isinstance(r.get("editorial_handoff"), dict):
                from mkt_flow_p0.editorial_identity import salvar_handoff_chatgpt
                try:
                    r["handoff_path"] = salvar_handoff_chatgpt(
                        r["editorial_handoff"], args.handoff_dir)
                except (ValueError, OSError) as exc:
                    r["handoff_error"] = str(exc)
                    logger.warning("Falha ao persistir handoff: %s", exc)
                    if args.handoff_only:
                        r["acao"] = "falha"
                        r["motivo"] = "erro_persistencia_handoff"
                        r["escreveu"] = False
            if args.handoff_dir and isinstance(r.get("editorial_trace"), dict):
                from mkt_flow_p0.editorial_trace import save_trace
                try:
                    r["trace_path"] = save_trace(r["editorial_trace"], args.handoff_dir)
                except (OSError, ValueError) as exc:
                    logger.error("Falha ao gravar trilha editorial: %s", type(exc).__name__)
                    # Do not claim full operational trace when persistence fails.
                    r["trace_error"] = "trace_persistence_failed"
                    if r.get("acao") in ("pacote_editorial_criado", "publicado_rascunho"):
                        r["acao"] = "falha"
                        r["motivo"] = "erro_persistencia_trilha"
                        # A draft might already exist: retain its original
                        # wrote flag and post_id, never retry the POST.
            if args.trace_db and isinstance(r.get("editorial_trace"), dict):
                try:
                    # The import happens in this cloud executor, not on the user's PC.
                    core_path = str(args.core_root.resolve())
                    if core_path not in sys.path:
                        sys.path.insert(0, core_path)
                    from editorial.trace_store import TraceStore
                    from editorial.trace_ingest import ingest_envelope
                    report = ingest_envelope(TraceStore(args.trace_db),
                                             r["editorial_trace"])
                    r["central_trace_synced"] = (
                        report["run_id"] == r["editorial_trace"]["run_id"])
                except (ImportError, OSError, ValueError, sqlite3.Error) as exc:
                    logger.error("Trilha central indisponivel: %s", type(exc).__name__)
                    r["central_trace_synced"] = False
                    r["trace_error"] = "central_trace_ingestion_failed"
                    if r.get("acao") in ("pacote_editorial_criado", "publicado_rascunho"):
                        r["acao"] = "falha"
                        r["motivo"] = "erro_ingestao_trilha"
                        # Preserve post_id for reconciliation of any written draft.
            if args.trace_turso and isinstance(r.get("editorial_trace"), dict):
                from mkt_flow_p0.editorial_trace_turso import save_turso_trace
                persistence = save_turso_trace(r["editorial_trace"])
                r["turso_trace_synced"] = persistence["ok"] is True
                if not r["turso_trace_synced"]:
                    r["trace_error"] = persistence["reason"]
                    if r.get("acao") in ("pacote_editorial_criado", "publicado_rascunho"):
                        r["acao"] = "falha"
                        r["motivo"] = "erro_persistencia_trilha_cloud"
                        # Preserve any preexisting WP draft and ID for reconciliation.
            if r["acao"] == "publicado_rascunho" and not args.dry_run:
                marcar_visto(fonte, item["link"], item["titulo"])
            total[r["acao"]] = total.get(r["acao"], 0) + 1
            print(json.dumps(resumo_seguro_cli(fonte, r), ensure_ascii=False))
    if contexto_pesquisa is not None and not contexto_usado:
        print(json.dumps({"aviso": "research_context_not_matched",
                          "source_url": contexto_pesquisa["source_url"]}, ensure_ascii=False))
    print(json.dumps({"resumo": total}, ensure_ascii=False))
    # Falha da fonte deve ser visível para o executor/agendador, mesmo sem itens.
    return 1 if (total["feed_error"] or total["falha"]) else 0


if __name__ == "__main__":
    sys.exit(main())
