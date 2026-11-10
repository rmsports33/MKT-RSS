import json
from pathlib import Path

import pytest

from tools.produce_bank_article import (
    HOMOLOG, ObservedModules, ProductionBlocked, load_brief, produce, require_credentials,
    missing_source_anchors,
)

BRIEF = Path(__file__).resolve().parents[1] / 'docs/briefs/CT-006.json'


def test_selected_brief_has_real_sources_and_no_publication_acceptance():
    brief = load_brief(BRIEF)
    assert brief['id'] == 'CT-006'
    assert brief['bank_priority'] == 'Alta'
    assert brief['image_candidate']['human_visual_review'] == 'PENDING'
    assert brief['publication_authorized'] is False
    assert len(brief['sources']) == 4


@pytest.mark.parametrize('field,value', [
    ('publication_authorized', True), ('bank_priority', 'Baixa'),
    ('source_url', 'https://attacker.example/source'),
])
def test_brief_scope_is_checked_before_execution(tmp_path, field, value):
    brief = json.loads(BRIEF.read_text())
    brief[field] = value
    path = tmp_path / 'brief.json'
    path.write_text(json.dumps(brief))
    with pytest.raises(ProductionBlocked, match='BRIEF_NOT_AUTHORIZED'):
        load_brief(path)


def test_unexpected_research_url_rejected(tmp_path):
    brief = json.loads(BRIEF.read_text())
    brief['sources'][0]['url'] = 'https://attacker.example/source'
    path = tmp_path / 'brief.json'
    path.write_text(json.dumps(brief))
    with pytest.raises(ProductionBlocked, match='SOURCES_NOT_AUTHORIZED'):
        load_brief(path)


def test_missing_credentials_never_fall_back_to_another_executor(monkeypatch):
    for key in ('GROQ_API_KEY', 'WP_USER', 'WP_APP_PASSWORD', 'TURSO_AUTH_TOKEN'):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(ProductionBlocked, match='PRODUCTION_CREDENTIALS_MISSING'):
        require_credentials()


def configure(monkeypatch):
    for key in ('GROQ_API_KEY', 'WP_USER', 'WP_APP_PASSWORD', 'TURSO_AUTH_TOKEN'):
        monkeypatch.setenv(key, 'test-placeholder')
    monkeypatch.setenv('WP_URL', 'https://conexotech.com.br')
    monkeypatch.setenv('TURSO_DATABASE_URL', 'libsql://' + HOMOLOG)
    monkeypatch.setenv('CONEXO_TRACE_TURSO_ALLOWED_HOST', HOMOLOG)


def test_other_database_rejected(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setenv('TURSO_DATABASE_URL', 'libsql://other.turso.io')
    with pytest.raises(ProductionBlocked, match='PRODUCTION_TARGET_MISMATCH'):
        require_credentials()


def test_expected_production_targets_accepted(monkeypatch):
    configure(monkeypatch)
    require_credentials()


def test_returned_gate_failure_stays_a_failure_not_an_approval():
    def blocked():
        return {'veredito': 'BLOQUEADO', 'motivos': ['contrato_ausente'],
                'content': 'UNPUBLISHED ARTICLE', 'prompt': 'PRIVATE PROMPT', 'token': 'SECRET'}
    observed = ObservedModules()
    observed.call('factual_review', blocked)
    event = observed.events[0]
    assert event['status'] == 'RETURNED'
    assert event['veredito'] == 'BLOQUEADO'
    encoded = json.dumps(event)
    assert not any(private in encoded for private in ('UNPUBLISHED', 'PRIVATE PROMPT', 'SECRET'))


def test_exception_details_do_not_leak_to_public_report():
    def fail():
        raise RuntimeError('SECRET in provider response')
    observed = ObservedModules()
    with pytest.raises(ProductionBlocked, match='MODULE_EXECUTION_FAILED') as exc:
        observed.call('generation', fail)
    assert 'SECRET' not in str(exc.value)
    assert 'SECRET' not in json.dumps(observed.events)
    assert observed.events[0]['status'] == 'FAILED'


@pytest.mark.parametrize('order_mode', ['server', 'rendered', 'unavailable'])
def test_production_integrates_private_draft_and_metadata_trace(monkeypatch, tmp_path, order_mode):
    from mkt_flow_p0 import (extractor, research_candidates, keyword_research, rewriter,
        related_posts, image_handler, wp_draft_staging, editorial_trace_turso)
    from mkt_flow_p0.editorial_identity import criar_handoff_chatgpt
    import requests
    import tools.wp_identity_preflight as identity
    configure(monkeypatch)
    from mkt_flow_p0 import editorial_development
    from test_editorial_substance import BRIEF as fixture_brief
    planned = dict(fixture_brief)
    planned['genre'] = load_brief(BRIEF)['genre']
    monkeypatch.setattr(editorial_development, 'plan_brief_with_provider', lambda *a, **kw: planned)
    # The repeated fixture is a pending draft, never a substantive PASS.
    monkeypatch.setattr(editorial_development, 'review_with_provider', lambda *a, **kw: None)
    brief = load_brief(BRIEF)
    private = 'PRIVATE ARTICLE BODY '
    body = ('Fonte completa para pesquisa. ' * 130
            + ' $499 $20,000 $200 Waitlist fourteen geographic website Payment information Privacy Choices 2026 2027')
    monkeypatch.setattr(identity, 'check_identity', lambda env: 'PASS')
    class Response:
        status_code = 200
        def json(self):
            return []
    monkeypatch.setattr(requests, 'get', lambda *a, **kw: Response())
    def extract(url, **kwargs):
        text = body
        if url.endswith('/order') and order_mode != 'server':
            if not kwargs.get('renderizar') or order_mode == 'unavailable':
                text = body.replace('$499', '').replace('$20,000', '')
        return {'texto': text, 'titulo': 'Fonte simulada somente neste teste', 'qualidade_ok': True,
                'origem': 'playwright_documento' if kwargs.get('renderizar') else 'html_documento'}
    monkeypatch.setattr(extractor, 'extrair_conteudo', extract)
    monkeypatch.setattr(research_candidates, 'descobrir_fontes_candidatas', lambda *a, **kw: {'sources': []})
    monkeypatch.setattr(keyword_research, 'sugerir_keywords_review', lambda *a, **kw: ['robô NEO'])
    generated = {'titulo_seo': brief['title'], 'texto_markdown': '## Texto\n' + private * 300,
        'slug': 'robo-neo', 'meta_description': 'Descricao editorial do robo NEO. ' * 5,
        'modelo': 'TEST_MODEL', 'prompt_sha256': 'a' * 64,
        'uso_tokens': {'prompt': 100, 'completion': 200, 'total': 300}}
    generated['editorial_handoff'] = criar_handoff_chatgpt(generated,
        url_fonte=brief['source_url'], fonte_nome=brief['source_name'],
        contexto_complementar={'sources': [{k: source[k] for k in ('name', 'url', 'facts')}
                                          for source in brief['sources']]})
    generations = []
    def generate(*args, **kwargs):
        generations.append(True)
        return generated
    monkeypatch.setattr(rewriter, 'reescrever_materia', generate)
    monkeypatch.setattr(related_posts, 'buscar_relacionados_wordpress', lambda *a, **kw: [])
    monkeypatch.setattr(image_handler, 'baixar_imagem', lambda *a, **kw: {'bytes': b'test image'})
    monkeypatch.setattr(image_handler, 'processar_capa', lambda *a, **kw:
        {'bytes': b'test JPEG', 'largura': 1200, 'altura': 675})
    monkeypatch.setattr(wp_draft_staging, 'stage_rss_draft', lambda **kw:
        {'acao': 'publicado_rascunho', 'status': 'draft', 'post_id': 12345})
    stored = {}
    def save(packet):
        stored.update(packet)
        return {'ok': True}
    monkeypatch.setattr(editorial_trace_turso, 'save_turso_trace', save)
    monkeypatch.setattr(editorial_trace_turso, 'get_turso_trace', lambda *a: {'ok': True, 'trace': stored})
    if order_mode == 'unavailable':
        with pytest.raises(ProductionBlocked, match='SOURCE_CHANGED_REQUIRES_RESEARCH'):
            produce(brief, tmp_path, execute_draft=True)
        report = json.loads((tmp_path / 'module-report.json').read_text())
        assert report['source_checks'][-1]['url'] == 'https://www.1x.tech/order'
        assert report['source_checks'][-1]['missing_anchors'] == ['$499', '$20,000']
        assert report['post_id'] is None and not generations and not stored
        return
    report = produce(brief, tmp_path, execute_draft=True)
    assert bool(order_mode == 'rendered') == any(
        event['stage'] == 'rendered_source_extraction' for event in report['modules'])
    assert report['post_id'] == 12345
    assert report['publication_authorized'] is False
    assert report['human_review'] == 'PENDING'
    assert report['outcome'] == 'DRAFT_READY_FOR_RESEARCH_REVIEW'
    assert (tmp_path / 'private-handoff.json').is_file()
    public_report = (tmp_path / 'module-report.json').read_text()
    assert private not in public_report
    assert body not in public_report
    assert 'test-placeholder' not in public_report
    assert any(event.get('veredito') == 'BLOQUEADO' for event in report['modules'])
    assert len(stored['events']) <= 64
    assert any(event.get('model_id') == 'TEST_MODEL' for event in stored['events'])


def test_source_anchors_accept_layout_whitespace_but_never_changed_values():
    assert missing_source_anchors('US$\u00a0499 / mês; $ 20,000; $200. Reserva.',
                                  ['$499', '$20,000', '$200']) == []
    assert missing_source_anchors('$4990 $20,000.50 $2000',
                                  ['$499', '$20,000', '$200']) == ['$499', '$20,000', '$200']
