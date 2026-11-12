"""Actual writer adapters, offline provider doubles; no editorial certification."""
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from mkt_flow_p0 import rewriter
from mkt_flow_p0.editorial_substance import GENRES
from src.generator.render import gerar_comparativo


def brief(genre='noticia'):
    return {
        'genre': genre,
        'reader': 'Leitores que precisam interpretar documentação técnica disponível.',
        'need': 'Identificar consequências e limites dos fatos fornecidos nas fontes.',
        'angle': 'Distinguir informação documentada de hipótese ainda não demonstrada.',
        'contribution': 'Explicar critérios práticos sustentados pelos documentos fornecidos.',
        'limits': 'Não inventar testes próprios, preços, medições ou experiências de uso.',
    }


@pytest.mark.parametrize('genre', sorted(GENRES))
def test_each_genre_reaches_actual_provider_adapter(monkeypatch, tmp_path, genre):
    create = Mock(return_value=SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({
            'texto_markdown': 'Texto de teste sem certificação factual. ' * 220,
            'titulo_seo': 'Documento técnico', 'slug': 'documento',
            'meta_description': 'Descrição sintética para testar o fluxo editorial com limites explícitos, sem certificar fontes, qualidade ou autorização de publicação.',
        })), finish_reason='stop')], usage=None))
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(rewriter, '_get_client', lambda: (client, ''))
    result = rewriter.reescrever_materia(
        'Documento técnico', 'Fonte de teste. ' * 120,
        editorial_brief=brief(genre), genre=genre)
    assert 'erro' not in result
    sent = create.call_args.kwargs['messages']
    assert brief(genre)['angle'] in sent[0]['content']
    assert f'"genre": "{genre}"' in sent[0]['content']


    from mkt_flow_p0.editorial_import import processar_artigo_importado
    payload = {
        'source_url': 'https://example.org/synthetic-source',
        'source_name': 'Fonte sintética de teste',
        'article': {key: result[key] for key in
                    ('titulo_seo', 'meta_description', 'slug', 'texto_markdown')},
        'research': {'sources': []}, 'editorial_brief': brief(genre),
    }
    processed = processar_artigo_importado(payload, tmp_path / genre, genero=genre)
    assert processed['publication_authorized'] is False
    assert processed['wordpress_written'] is False
    assert processed['human_acceptance'] == 'PENDING'
    assert {'editorial_substance', 'image_protocol', 'seo', 'format',
            'editorial_readiness', 'editorial_trace'} <= set(processed['modules_executed'])


@pytest.mark.parametrize('value', [None, {}, {'genre': 'noticia'}])
def test_missing_or_invalid_brief_never_opens_provider(monkeypatch, value):
    client = Mock(side_effect=AssertionError('provider must not open'))
    monkeypatch.setattr(rewriter, '_get_client', client)
    result = rewriter.reescrever_materia('Título', 'Insumo completo. ' * 120,
                                         editorial_brief=value)
    assert 'erro' in result
    client.assert_not_called()


def test_cross_genre_brief_never_opens_provider(monkeypatch):
    client = Mock(side_effect=AssertionError('provider must not open'))
    monkeypatch.setattr(rewriter, '_get_client', client)
    result = rewriter.reescrever_materia('Título', 'Insumo completo. ' * 120,
                                         editorial_brief=brief('guia'), genre='review')
    assert 'erro' in result
    client.assert_not_called()


def test_comparative_missing_brief_blocks_even_force_override():
    provider = Mock()
    with pytest.raises(ValueError, match='briefing editorial'):
        gerar_comparativo([], chamar_llm=provider, forcar=True)
    provider.assert_not_called()


@pytest.mark.parametrize('supplied', [None, {}, brief('review')])
def test_rss_invalid_planning_never_enters_writer(monkeypatch, supplied):
    import pipeline_rss
    from mkt_flow_p0 import extractor, seo, editorial_development
    monkeypatch.setattr(extractor, 'extrair_conteudo', lambda _: {
        'titulo': 'Notebook recebe atualização', 'texto': 'Documentação técnica. ' * 120,
        'palavras': 240, 'qualidade_ok': True})
    monkeypatch.setattr(seo, 'enriquecer_com_keywords', lambda *a, **kw: [])
    planner = Mock(side_effect=ValueError('provider unavailable'))
    monkeypatch.setattr(editorial_development, 'plan_brief_with_provider', planner)
    writer = Mock(side_effect=AssertionError('writer must not run'))
    monkeypatch.setattr(rewriter, 'reescrever_materia', writer)
    item = {'titulo': 'Notebook recebe atualização', 'resumo': 'Atualização de aplicativos',
            'link': 'https://fonte.example/notebook', 'fonte': 'Fonte sintética',
            'editorial_brief': supplied}
    result = pipeline_rss.processar_item(item)
    assert result['acao'] == 'falha'
    assert 'Briefing editorial' in result['motivo']
    assert result['editorial_trace']
    writer.assert_not_called()
