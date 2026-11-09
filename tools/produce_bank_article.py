"""Run the existing editorial modules for one researched bank topic.

This produces one private draft and an honest module report, never an approval
or a publication. Public output contains metadata only; source bodies, generated
text and prompts stay in the private runner workspace / WordPress draft.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import uuid

SITE = 'https://conexotech.com.br'
HOMOLOG = 'mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io'


class ProductionBlocked(Exception):
    pass


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def load_brief(path):
    brief = json.loads(Path(path).read_text(encoding='utf-8'))
    if (brief.get('id') != 'CT-006' or brief.get('bank_priority') != 'Alta'
            or brief.get('publication_authorized') is not False
            or brief.get('source_url') != 'https://www.1x.tech/discover/neo-home-robot'
            or not isinstance(brief.get('sources'), list) or len(brief['sources']) != 4):
        raise ProductionBlocked('BRIEF_NOT_AUTHORIZED')
    expected = {'https://www.1x.tech/order', 'https://www.1x.tech/legal',
                'https://www.1x.tech/privacy-policy', 'https://www.1x.tech/about'}
    if {s.get('url') for s in brief['sources']} != expected:
        raise ProductionBlocked('SOURCES_NOT_AUTHORIZED')
    return brief


def require_credentials():
    from urllib.parse import urlsplit
    required = ['GROQ_API_KEY', 'WP_USER', 'WP_APP_PASSWORD', 'TURSO_AUTH_TOKEN']
    if any(not os.getenv(name, '').strip() for name in required):
        raise ProductionBlocked('PRODUCTION_CREDENTIALS_MISSING')
    if (os.getenv('WP_URL', '').rstrip('/') != SITE
            or urlsplit(os.getenv('TURSO_DATABASE_URL', '')).hostname != HOMOLOG
            or os.getenv('CONEXO_TRACE_TURSO_ALLOWED_HOST') != HOMOLOG):
        raise ProductionBlocked('PRODUCTION_TARGET_MISMATCH')


class ObservedModules:
    def __init__(self):
        self.events = []

    def call(self, stage, function, *args, **kwargs):
        event = {'stage': stage, 'module_id': function.__module__ + '.' + function.__name__,
                 'status': 'STARTED', 'started_at': datetime.now(timezone.utc).isoformat()}
        self.events.append(event)
        try:
            result = function(*args, **kwargs)
        except Exception:
            event['status'] = 'FAILED'
            raise ProductionBlocked('MODULE_EXECUTION_FAILED') from None
        event['status'] = 'RETURNED'
        if isinstance(result, dict):
            for key in ('veredito', 'status', 'motivos', 'pendencias', 'palavras', 'nota', 'qualidade_ok',
                        'faixa', 'modelo', 'prompt_sha256', 'uso_tokens'):
                if key in result:
                    event[key if key != 'status' else 'result_status'] = result[key]
            if 'erro' in result:
                event['result_status'] = 'ERROR'
        event['finished_at'] = datetime.now(timezone.utc).isoformat()
        return result


def produce(brief, output_dir, *, execute_draft=False):
    if execute_draft:
        require_credentials()
    from mkt_flow_p0.prioridade_editorial import avaliar_pauta
    from mkt_flow_p0.content_filter import filtrar_por_tema, filtrar_item_rss, filtrar_conteudo, gate_publicacao
    from mkt_flow_p0.extractor import extrair_conteudo
    from mkt_flow_p0.captura_completa import criar_captura_completa
    from mkt_flow_p0.research_candidates import descobrir_fontes_candidatas
    from mkt_flow_p0.keyword_research import sugerir_keywords_review
    from mkt_flow_p0.rewriter import reescrever_materia, adicionar_atribuicao
    from mkt_flow_p0.related_posts import buscar_relacionados_wordpress, anexar_relacionados
    from mkt_flow_p0.image_handler import baixar_imagem, processar_capa
    from mkt_flow_p0.editorial_identity import atualizar_handoff_revisao, validar_handoff_chatgpt
    from mkt_flow_p0.format import markdown_para_html
    from mkt_flow_p0.editorial_readiness import avaliar_prontidao_editorial
    from mkt_flow_p0.gate_editorial_pos_ia import validar_saida
    from mkt_flow_p0.adaptador_contrato_editorial import avaliar_snapshot_editorial
    from mkt_flow_p0.lastro_offline_noticia import auditar_lastro_offline
    from mkt_flow_p0.auditoria_cobertura_pos_ia import auditar_cobertura_pos_ia
    from mkt_flow_p0.editorial_trace import make_trace
    from mkt_flow_p0.editorial_trace_turso import save_turso_trace, get_turso_trace
    from mkt_flow_p0.wp_draft_staging import stage_rss_draft
    from tools.wp_identity_preflight import check_identity
    from mkt_flow_p0.seo import validar_seo_qualidade

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    observed = ObservedModules()
    report = {'schema': 'conexo-bank-production-report/1', 'bank_id': brief['id'],
              'run_id': str(uuid.uuid4()), 'post_id': None, 'publication_authorized': False,
              'human_review': 'PENDING', 'modules': observed.events,
              'not_applicable': {
                  'feed_collection': 'Existing topic read from the official Drive bank; RSS is used for supplementary discovery only.',
                  'video_review': 'Selected evidence consists of text pages; no video observation is claimed.',
                  'image_generation': 'An existing free stock candidate was identified.',
                  'publication_and_signed_seo': 'This request creates a draft; human approval and publication are separate.'}}
    try:
        if execute_draft:
            if observed.call('publisher_identity', check_identity, os.environ) != 'PASS':
                raise ProductionBlocked('MKT_IDENTITY_NOT_CONFIRMED')
            # Check the existing deterministic staging slug before spending
            # tokens. Never replace an existing draft with a fresh generation.
            import requests
            from mkt_flow_p0.wp_draft_staging import _slug
            response = requests.get(SITE + '/wp-json/wp/v2/posts',
                params={'slug': _slug(brief['title'], brief['source_url']),
                        'status': 'draft,pending,publish,future,private', 'context': 'edit',
                        '_fields': 'id,status'},
                auth=(os.environ['WP_USER'], os.environ['WP_APP_PASSWORD']),
                timeout=15, allow_redirects=False)
            if response.status_code != 200 or not isinstance(response.json(), list):
                raise ProductionBlocked('DRAFT_DEDUP_READ_FAILED')
            if response.json():
                report['existing_post_id'] = response.json()[0].get('id')
                raise ProductionBlocked('EXISTING_ARTICLE_INSPECT_FIRST_NO_RETRY')
        observed.call('priority', avaliar_pauta, {'titulo': brief['title']})
        item = {'titulo': brief['title'], 'resumo': brief['summary'],
                'link': brief['source_url'], 'fonte': brief['source_name']}
        for name, fn, args in [('topic_filter', filtrar_por_tema, (brief['title'], brief['summary'])),
                               ('source_filter', filtrar_item_rss, (item,))]:
            verdict = observed.call(name, fn, *args)
            if verdict.get('veredito') == 'BLOQUEADO':
                raise ProductionBlocked('SOURCE_FILTER_BLOCKED')
        captures = {}
        originals = [{'url': brief['source_url'], 'name': brief['source_name']}] + brief['sources']
        for source in originals:
            extracted = observed.call('source_extraction', extrair_conteudo, source['url'], min_palavras=100)
            if extracted.get('erro') or not extracted.get('qualidade_ok'):
                raise ProductionBlocked('FULL_SOURCE_UNAVAILABLE')
            body = extracted['texto']
            if any(anchor.casefold() not in body.casefold() for anchor in source.get('anchors', [])):
                raise ProductionBlocked('SOURCE_CHANGED_REQUIRES_RESEARCH')
            capture = observed.call('source_capture', criar_captura_completa,
                                    source['url'], body, titulo=extracted.get('titulo') or source['name'])
            captures[source['url']] = capture
        # Related RSS discovery is observed even when it finds no candidate.
        discovered = observed.call('rss_research', descobrir_fontes_candidatas,
                                   brief['title'], brief['source_url'], max_feeds=3)
        report['rss_candidate_count'] = len(discovered.get('sources', []))
        keywords = observed.call('keyword_research', sugerir_keywords_review, 'robô NEO 1X', limit=8)
        report['keywords'] = keywords
        report['keywords_note'] = 'Autocomplete may use built-in seeds; no search volume was measured.'
        context = {'sources': [{k: source[k] for k in ('name', 'url', 'facts')} for source in brief['sources']]}
        original = captures[brief['source_url']]['texto']
        observed.call('added_value_gate', gate_publicacao,
                       brief['title'], '\n\n'.join(capture['texto'] for capture in captures.values()),
                       [source['url'] for source in originals])
        source_verdict = observed.call('extracted_content_filter', filtrar_conteudo,
                                       brief['title'], original)
        if source_verdict.get('veredito') == 'BLOQUEADO':
            raise ProductionBlocked('EXTRACTED_SOURCE_FILTER_BLOCKED')
        generated = observed.call('generation', reescrever_materia, brief['title'], original,
                                  fonte_nome=brief['source_name'], url_fonte=brief['source_url'],
                                  keywords=keywords, contexto_complementar=context, max_tokens=5000,
                                  timeout=90, temperature=0.3)
        if generated.get('erro'):
            raise ProductionBlocked('GENERATION_NOT_CONFIRMED')
        content_verdict = observed.call('generated_content_filter', filtrar_conteudo,
                                        generated['titulo_seo'], generated['texto_markdown'])
        if content_verdict.get('veredito') == 'BLOQUEADO':
            raise ProductionBlocked('GENERATED_CONTENT_FILTER_BLOCKED')
        markdown = observed.call('source_attribution', adicionar_atribuicao,
                                 generated['texto_markdown'], brief['source_name'], brief['source_url'])
        related = observed.call('internal_links', buscar_relacionados_wordpress, brief['related_query'], SITE)
        markdown = observed.call('internal_link_format', anexar_relacionados, markdown, related)
        report['related_urls'] = [entry['url'] for entry in related]
        handoff = observed.call('versioned_package', atualizar_handoff_revisao,
                                generated['editorial_handoff'], markdown, related_articles=related)
        observed.call('package_integrity', validar_handoff_chatgpt, handoff)
        html = observed.call('html_format', markdown_para_html, markdown)
        report['wordpress_content_sha256'] = digest(html)
        # Preview checks use the actual deterministic draft slug, not a made-up
        # public URL or a claim that native signed SEO has already been deployed.
        from html import escape
        from mkt_flow_p0.wp_draft_staging import _slug
        canonical = SITE + '/' + _slug(generated['titulo_seo'], brief['source_url']) + '/'
        seo_preview = ('<html><head><title>' + escape(generated['titulo_seo']) + '</title>'
                       '<meta name="description" content="' + escape(generated['meta_description'], quote=True)
                       + '"><link rel="canonical" href="' + canonical + '"></head><body>' + html + '</body></html>')
        observed.call('seo_preview_quality', validar_seo_qualidade, seo_preview)
        report['seo_preview_canonical'] = canonical
        (output / 'private-handoff.json').write_text(json.dumps(handoff, ensure_ascii=False), encoding='utf-8')
        (output / 'private-sources.json').write_text(json.dumps(captures, ensure_ascii=False), encoding='utf-8')
        # An actual licensed-stock candidate is processed, but no human media
        # acceptance or permission to attach it to the draft is fabricated.
        image = brief['image_candidate']
        downloaded = observed.call('image_download', baixar_imagem, image['url'])
        if downloaded.get('erro'):
            raise ProductionBlocked('IMAGE_CANDIDATE_UNAVAILABLE')
        cover = observed.call('image_processing', processar_capa, downloaded['bytes'])
        if cover.get('erro'):
            raise ProductionBlocked('IMAGE_PROCESSING_FAILED')
        (output / 'cover-candidate.jpg').write_bytes(cover['bytes'])
        report['image_candidate'] = {k: v for k, v in image.items() if k != 'url'}
        report['image_candidate']['dimensions'] = [cover['largura'], cover['altura']]
        report['image_candidate']['sha256'] = hashlib.sha256(cover['bytes']).hexdigest()
        # Execute the existing diagnostic gates without promoting missing
        # independently reviewed claim contracts to PASS.
        observed.call('post_generation_review', validar_saida, original, generated['texto_markdown'])
        contract = generated.get('contrato_editorial')
        observed.call('evidence_contract', avaliar_snapshot_editorial, contract)
        observed.call('source_grounding', auditar_lastro_offline, contract, captures)
        observed.call('claim_coverage', auditar_cobertura_pos_ia,
                      generated['texto_markdown'], contract, captures, generated.get('referencias_traducao'))
        readiness = observed.call('editorial_readiness', avaliar_prontidao_editorial,
                                  handoff, html=html, genero=brief['genre'],
                                  verified_related_urls=report['related_urls'])
        report['readiness'] = readiness
        report['version_sha256'] = handoff['version_sha256']
        report['source_hashes'] = {url: capture['sha256_texto'] for url, capture in captures.items()}
        if execute_draft:
            staged = observed.call('draft_delivery', stage_rss_draft, title=generated['titulo_seo'],
                                   content=html, source_url=brief['source_url'], wp_url=SITE,
                                   wp_user=os.environ['WP_USER'], wp_password=os.environ['WP_APP_PASSWORD'],
                                   excerpt=generated['meta_description'], author_id=3)
            if staged.get('acao') != 'publicado_rascunho' or staged.get('status') != 'draft':
                # Could already exist or be an indeterminate POST; never retry.
                report['draft_outcome'] = staged.get('acao')
                raise ProductionBlocked('DRAFT_NOT_CONFIRMED_INSPECT_BEFORE_RETRY')
            report['post_id'] = staged['post_id']
            trace = make_trace(brief['source_url'], markdown, generated=generated,
                               readiness=readiness, post_id=staged['post_id'], wp_readback=True)
            trace['events'].extend([{**event, 'evidence_ref': 'bank-production:' + report['run_id']}
                                    for event in observed.events])
            report['trace_run_id'] = trace['run_id']
            saved = observed.call('trace_storage', save_turso_trace, trace)
            if saved.get('ok') is not True:
                raise ProductionBlocked('DRAFT_CREATED_TRACE_STORAGE_PENDING_NO_RETRY')
            read = observed.call('trace_readback', get_turso_trace, trace['run_id'])
            if read.get('ok') is not True or read.get('trace') != trace:
                raise ProductionBlocked('DRAFT_CREATED_TRACE_READBACK_PENDING_NO_RETRY')
        report['outcome'] = 'DRAFT_READY_FOR_RESEARCH_REVIEW' if execute_draft else 'LOCAL_HANDOFF_ONLY'
        return report
    except ProductionBlocked as exc:
        report['outcome'] = str(exc)
        raise
    finally:
        # Report never contains the draft, prompts, raw source bodies or secrets.
        (output / 'module-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--brief', type=Path, default=Path('docs/briefs/CT-006.json'))
    parser.add_argument('--output-dir', type=Path, default=Path('work/bank-production'))
    parser.add_argument('--execute-draft', action='store_true')
    args = parser.parse_args()
    # Existing modules can log provider/transport exceptions; keep private
    # material out of public Actions logs. This runner prints stable codes only.
    logging.disable(logging.CRITICAL)
    try:
        result = produce(load_brief(args.brief), args.output_dir, execute_draft=args.execute_draft)
    except ProductionBlocked as exc:
        print(json.dumps({'outcome': str(exc), 'retry_automatic': False}))
        return 1
    except Exception:
        print(json.dumps({'outcome': 'PRODUCTION_UNKNOWN_INSPECT_BEFORE_RETRY', 'retry_automatic': False}))
        return 1
    print(json.dumps({k: result[k] for k in ('bank_id', 'outcome', 'post_id', 'human_review', 'trace_run_id')
                      if k in result}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
