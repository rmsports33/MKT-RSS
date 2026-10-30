"""Homologação offline: HTTP simulado, sockets proibidos, SQLite temporário."""
import copy
import json
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from mkt_flow_p0.price_api_clients import MercadoLivreClient, PriceAPIError
from mkt_flow_p0 import price_collector as pc
from mkt_flow_p0.comparativo_flow import processar_comparativo

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'redator-artigo-blogs'))
from src.generator.render import gerar_comparativo

TOKEN = 'token-ficticio-segredo'


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    def deny(*a, **k):
        pytest.fail('socket/HTTP real proibido na homologacao')
    monkeypatch.setattr(socket, 'socket', deny)
    monkeypatch.setattr(requests.sessions.Session, 'request', deny)
    monkeypatch.setattr(pc, '_DB_PATH', tmp_path / 'evidence.sqlite')
    monkeypatch.setattr(pc, '_CREDS', pc._Credenciais())
    pc._CREDS.amazon = dict.fromkeys(pc._CREDS.amazon, '')
    pc._CREDS.mercadolivre = dict.fromkeys(pc._CREDS.mercadolivre, '')
    pc._CREDS.shopee = dict.fromkeys(pc._CREDS.shopee, '')


def payload(item_id='MLB123'):
    return dict(id=item_id, site_id='MLB', currency_id='BRL', status='active',
                price=1500.5, permalink='https://produto.mercadolivre.com.br/' + item_id)


def response(code=200, data=None, headers=None):
    r = Mock(status_code=code, headers=headers or {})
    r.json.return_value = payload() if data is None else data
    return r


def client(*responses, token=TOKEN):
    session = Mock()
    session.get.side_effect = responses or [response()]
    sleep = Mock()
    c = MercadoLivreClient(token, session=session, sleep=sleep,
                          now=lambda: datetime(2026, 10, 30, tzinfo=timezone.utc))
    return c, session, sleep


def test_valid_response_and_auth():
    c, s, _ = client(response())
    assert c.get_item('MLB123')['preco'] == '1500.5'
    assert s.get.call_args.kwargs['headers'] == {'Authorization': 'Bearer ' + TOKEN}
    assert s.get.call_args.kwargs['allow_redirects'] is False


@pytest.mark.parametrize('token', ['', '\rsecret', '\nsecret'])
def test_missing_credentials_no_http(token):
    c, s, _ = client(token=token)
    with pytest.raises(PriceAPIError): c.get_item('MLB123')
    s.get.assert_not_called()


@pytest.mark.parametrize('item', ['MLB../1', 'MLA123', '', None])
def test_bad_id_no_http(item):
    c, s, _ = client()
    with pytest.raises(PriceAPIError): c.get_item(item)
    s.get.assert_not_called()


@pytest.mark.parametrize('code', [401, 403, 404, 302])
def test_terminal_http_no_retry(code):
    c, s, _ = client(response(code))
    with pytest.raises(PriceAPIError, match=str(code)): c.get_item('MLB123')
    assert s.get.call_count == 1


@pytest.mark.parametrize('failure', [429, 500, 502, 503, 504, 'timeout'])
def test_retry_then_success(failure):
    first = requests.Timeout(TOKEN) if failure == 'timeout' else response(failure)
    c, s, sleep = client(first, response())
    assert c.get_item('MLB123')['item_id'] == 'MLB123'
    assert s.get.call_count == 2
    sleep.assert_any_call(1)


def test_retry_exhaustion_sanitized():
    c, s, _ = client(*[requests.Timeout(TOKEN)] * 3)
    with pytest.raises(PriceAPIError) as e: c.get_item('MLB123')
    assert TOKEN not in str(e.value)
    assert s.get.call_count == 3


@pytest.mark.parametrize('header', ['2', 'Fri, 30 Oct 2026 00:00:02 GMT'])
def test_retry_after(header):
    c, s, sleep = client(response(429, headers={'Retry-After': header}), response())
    c.get_item('MLB123')
    sleep.assert_any_call(2)


@pytest.mark.parametrize('header', ['999', 'NaN', 'bad'])
def test_excessive_or_invalid_retry_after_blocks(header):
    c, s, _ = client(response(429, headers={'Retry-After': header}))
    with pytest.raises(PriceAPIError): c.get_item('MLB123')
    assert s.get.call_count == 1


@pytest.mark.parametrize('key,value', [('id','MLB999'), ('site_id','MLA'),
    ('currency_id','USD'), ('status','paused'), ('price',True), ('price',0),
    ('price',-1), ('price','NaN'), ('price','Infinity'), ('price',None),
    ('permalink','https://evil.test/a'), ('permalink','http://www.mercadolivre.com.br/a'),
    ('permalink','https://www.mercadolivre.com.br.evil.test/a')])
def test_invalid_payload_blocks(key, value):
    data = payload(); data[key] = value
    c, _, _ = client(response(data=data))
    with pytest.raises(PriceAPIError): c.get_item('MLB123')


def test_invalid_json():
    r = response(); r.json.side_effect = ValueError(TOKEN)
    c, _, _ = client(r)
    with pytest.raises(PriceAPIError, match='JSON'): c.get_item('MLB123')


def test_interval_between_items():
    c, _, sleep = client(response(), response())
    c.clock = lambda: 0
    c.get_item('MLB123'); c.get_item('MLB123')
    sleep.assert_any_call(1)


def test_collector_credentials_loaded(monkeypatch):
    monkeypatch.setenv('MERCADOLIVRE_ACCESS_TOKEN', TOKEN)
    assert pc._Credenciais().tem_mercadolivre()


def test_app_id_secret_alone_not_credentials():
    pc._CREDS.mercadolivre.update(app_id='123', client_secret=TOKEN)
    assert not pc._CREDS.tem_mercadolivre()
    assert not pc.coletar_preco_produto('A', ml_item_id='MLB123')['ok']


def test_collector_rejects_invalid_identity_source_and_date():
    """Qualquer transporte, inclusive mock, deve preservar identidade e prova."""
    original = dict(preco='1500.5', data_captura='30/10/2026',
                    url='https://produto.mercadolivre.com.br/MLB123',
                    item_id='MLB123', marketplace='mercadolivre')
    invalidos = [
        {'item_id': 'MLB999'},
        {'item_id': None},
        {'marketplace': 'amazon'},
        {'url': 'https://produto.mercadolivre.com.br.evil.test/MLB123'},
        {'url': 'http://produto.mercadolivre.com.br/MLB123'},
        {'url': 'https://usuario@produto.mercadolivre.com.br/MLB123'},
        {'data_captura': None},
        {'data_captura': '31/02/2026'},
    ]
    for alteracao in invalidos:
        client_fake = Mock()
        client_fake.get_item.return_value = dict(original, **alteracao)
        result = pc.coletar_preco_produto('A', ml_item_id='MLB123',
                                          client=client_fake)
        assert result['ok'] is False, alteracao
        assert not pc._DB_PATH.exists(), alteracao


def test_collector_chain_and_no_persistence():
    c, _, _ = client(response())
    ph = pc.gerar_price_history_para_modelos([{'nome':'A','ml_id':'MLB123'}], client=c)
    assert ph['A'][0]['preco'] == '1.500,50'
    assert ph['A'][0]['data'] == '30/10/2026'
    assert not pc._DB_PATH.exists()


@pytest.mark.parametrize('value', [0,-1,float('nan'),float('inf'),True])
def test_invalid_prices(value):
    assert pc.normalizar_preco(value) == ''


def test_explicit_persistence_identity_and_redaction():
    import sqlite3
    c, _, _ = client(response())
    assert pc.coletar_preco_produto('Nome correto', ml_item_id='MLB123', client=c, persistir=True)['ok']
    with sqlite3.connect(pc._DB_PATH) as db:
        assert db.execute('select produto from price_evidence').fetchone()[0] == 'Nome correto'
    pc._salvar_evidencia('A','mercadolivre','R$ 1,00','30/10/2026',
                        'https://www.mercadolivre.com.br/a', {'access_token':TOKEN})
    assert TOKEN.encode() not in pc._DB_PATH.read_bytes()


def test_end_to_end_offline_two_products(monkeypatch):
    wp = Mock(side_effect=AssertionError('WordPress proibido em dry-run'))
    monkeypatch.setattr('mkt_flow_p0.wp_publisher.publicar_comparativo', wp)
    data = json.loads((Path(__file__).resolve().parents[2] / 'tools/exemplo_comparativo_m0417d.json').read_text())
    models = data['modelos']
    models[0]['ml_id']='MLB123'; models[1]['ml_id']='MLB456'
    c, s, _ = client(response(), response(data=payload('MLB456')))
    rendered = gerar_comparativo(models, coletar_precos=True, cliente_precos=c,
                                chamar_llm=lambda *a: '<h2>Comparação</h2><p>Fichas documentais.</p>')
    assert 'erro' not in rendered
    data['price_history']=rendered['price_history']
    data['conteudo_html']=rendered['html']
    data.pop('_comentario')
    result = processar_comparativo(**data)
    assert result['acao'] == 'dry_run_ok'
    assert result['escreveu'] is False
    wp.assert_not_called()
    assert s.get.call_count == 2
    assert not pc._DB_PATH.exists()
    # Evidência inválida em ambos os produtos bloqueia antes do WordPress.
    for key, value in [('data','31/02/2026'), ('fonte',''), ('preco','invalido'), ('produto','Outro')]:
        broken = copy.deepcopy(data)
        for points in broken['price_history'].values(): points[0][key]=value
        assert processar_comparativo(**broken)['acao'] == 'bloqueado'


def test_incomplete_collection_blocks_before_llm():
    llm=Mock()
    c, _, _ = client(response(403))
    result=gerar_comparativo([{'nome':'A','ml_id':'MLB123'}],
                            coletar_precos=True, cliente_precos=c, chamar_llm=llm)
    assert 'BLOQUEADO' in result['erro']
    llm.assert_not_called()


def test_collection_is_explicit_opt_in():
    c=Mock()
    gerar_comparativo([{'nome':'A','specs':{}}], cliente_precos=c,
                     chamar_llm=lambda *a: '<p>Ficha documental.</p>')
    c.get_item.assert_not_called()


def test_unimplemented_marketplaces_never_request():
    pc._CREDS.amazon = dict.fromkeys(pc._CREDS.amazon, 'ficticio')
    pc._CREDS.shopee = dict.fromkeys(pc._CREDS.shopee, 'ficticio')
    assert pc._CREDS.marketplaces_disponiveis() == []
    assert not pc.coletar_preco_produto('A', asin='B0XXX')['ok']
    assert not pc.coletar_preco_produto('A', shopee_item_id='1', shopee_shop_id='2')['ok']


def test_duplicate_model_identity_blocks_before_collection():
    c = Mock()
    result = gerar_comparativo([{'nome':'A'}, {'nome':'a'}], coletar_precos=True,
                               cliente_precos=c, chamar_llm=Mock())
    assert 'BLOQUEADO' in result['erro']
    c.get_item.assert_not_called()



def test_cli_with_mocked_ml_is_independent_of_late_imports(monkeypatch, capsys):
    """Execução como __main__ deve preparar todos os imports antes da CLI."""
    import runpy
    monkeypatch.setenv('MERCADOLIVRE_ACCESS_TOKEN', TOKEN)
    monkeypatch.setattr(sys, 'argv', [
        'price_collector', '--produto', 'A', '--ml-id', 'MLB123',
    ])
    mocked_get = Mock(return_value=response())
    monkeypatch.setattr(requests.sessions.Session, 'get', mocked_get)
    with pytest.raises(SystemExit) as done:
        runpy.run_module('mkt_flow_p0.price_collector', run_name='__main__')
    assert done.value.code == 0
    assert mocked_get.call_count == 1
    output = capsys.readouterr().out
    assert '"ok": true' in output
    assert TOKEN not in output


def test_environment_client_reused_for_all_products(monkeypatch):
    # Caminho normal: sem injetar client no helper; só o transporte é simulado.
    session = Mock()
    session.get.side_effect = [response(), response(data=payload('MLB456'))]
    constructor = Mock(return_value=session)
    monkeypatch.setattr('mkt_flow_p0.price_api_clients.requests.Session', constructor)
    pc._CREDS.mercadolivre['access_token'] = TOKEN
    ph = pc.gerar_price_history_para_modelos([
        {'nome':'A','ml_id':'MLB123'}, {'nome':'B','ml_id':'MLB456'}])
    assert set(ph) == {'A','B'}
    assert session.get.call_count == 2
    constructor.assert_called_once()
    assert all(call.kwargs['headers']['Authorization'] == 'Bearer ' + TOKEN
               for call in session.get.call_args_list)
    assert not pc._DB_PATH.exists()
