"""Offline regression for ChatGPT/MKT-RSS import; no fixtures, network or WP."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from mkt_flow_p0.editorial_import import importar_artigo_para_handoff
from mkt_flow_p0.editorial_identity import validar_handoff_chatgpt


def sample():
    return {
        'source_url': 'https://developer.android.com/ai/appfunctions',
        'source_name': 'Android Developers',
        'article': {
            'titulo_seo': 'Funcoes Android para assistentes de IA',
            'meta_description': 'Panorama tecnicamente verificavel para brasileiros.',
            'slug': 'android-funcoes-ia',
            'texto_markdown': '## Android\n\n' + ('Explicação fundamentada na documentação, com limites e contexto brasileiro. ' * 28),
        },
        'research': {'sources': [
            {'name': 'Fonte adicional', 'url': 'https://developer.android.com/blog',
             'facts': ['A documentação diferencia funcionalidades disponíveis e experimentais.']}
        ]},
    }


def test_import_readback_idempotent_and_pending(tmp_path):
    data = sample()
    a = importar_artigo_para_handoff(data, tmp_path)
    assert a['valid'] and a['provider_called'] is False and a['wordpress_written'] is False
    assert a['source_count'] == 2 and a['claims_pending'] == 1
    assert a['review_status'] == 'PENDING_HUMAN_REVIEW'
    saved = json.loads(Path(a['handoff_path']).read_text(encoding='utf-8'))
    assert validar_handoff_chatgpt(saved)['version_sha256'] == a['version_sha256']
    assert importar_artigo_para_handoff(data, tmp_path) == a
    assert len(list(tmp_path.glob('*.json'))) == 1


def test_change_creates_new_version_not_new_approval(tmp_path):
    a = sample()
    b = deepcopy(a)
    b['article']['texto_markdown'] += '\n\nInformação adicional.'
    x = importar_artigo_para_handoff(a, tmp_path)
    y = importar_artigo_para_handoff(b, tmp_path)
    assert x['version_sha256'] != y['version_sha256']
    assert len(list(tmp_path.glob('*.json'))) == 2
    assert y['review_status'] == 'PENDING_HUMAN_REVIEW'


@pytest.mark.parametrize('tamper', [
    lambda x: x.update(source_url='http://insecure.example/article'),
    lambda x: x.update(source_name=''),
    lambda x: x['article'].update(texto_markdown='muito curto'),
    lambda x: x['article'].update(unexpected='foo'),
    lambda x: x['research']['sources'][0].update(url='https://user:password@example.com/a'),
    lambda x: x.pop('research'),
])
def test_invalid_input_does_not_write(tmp_path, tamper):
    data = sample()
    tamper(data)
    with pytest.raises(ValueError):
        importar_artigo_para_handoff(data, tmp_path)
    assert not list(tmp_path.iterdir())
