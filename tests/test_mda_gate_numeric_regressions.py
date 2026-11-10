"""Regressions from real MDA A/B run 42917583190; offline and non-approving."""
import pytest
from mkt_flow_p0.gate_editorial_pos_ia import validar_saida

@pytest.mark.parametrize('source,draft', [
    ('A fonte tem 1.799 participantes e 85% de respostas.',
     'A amostra teve 1 799 participantes e 85 % de respostas.'),
    ('A capacidade é de 5.000 mAh.', 'A bateria tem 5\u202f000mAh.'),
    ('Sem números ou medidas de teste.',
     '### 1. Confira o sintoma\n\n### 2. Revise o efeito\n\n3) Volte se preciso'),
])
def test_formatting_changes_are_not_numeric_facts(source, draft):
    report = validar_saida(source, draft)
    assert report['numeros_novos'] == []

@pytest.mark.parametrize('source,draft,unexpected', [
    ('A Samsung informa vídeo em Full HD 1080p.', 'O Galaxy A16 grava em 4K.', '4k'),
    ('Sem dados comerciais divulgados.', 'O preço custa US$ 110 por mês.', 'us$ 110'),
    ('Uma bateria com 5.000mAh.', 'Uma bateria de 6.000mAh.', '6.000mah'),
])
def test_new_quantities_remain_blocked(source, draft, unexpected):
    report = validar_saida(source, draft)
    assert report['veredito'] == 'BLOQUEADO'
    assert unexpected in report['numeros_novos']


def test_numeric_preflight_is_not_factual_approval():
    report = validar_saida('Teclado preditivo e previsões em linha.',
                           'Desligue o recurso que deseja preservar.')
    assert report['veredito'] == 'SEM_ALERTAS'
    # Important: a green numeric report cannot prove semantic correctness.