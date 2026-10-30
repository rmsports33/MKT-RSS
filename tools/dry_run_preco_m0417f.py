"""Prova sintética ML -> coletor -> redator -> contrato -> gate, sem rede/escrita.
Execute a partir da raiz: python tools/dry_run_preco_m0417f.py
"""
import json
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'redator-artigo-blogs'))
from mkt_flow_p0.price_api_clients import MercadoLivreClient
from mkt_flow_p0.comparativo_flow import processar_comparativo
from src.generator.render import gerar_comparativo


class FixtureSession:
    def __init__(self):
        self.calls = 0

    def get(self, url, **kwargs):
        self.calls += 1
        item = url.rsplit('/', 1)[-1]
        class Response:
            status_code = 200
            headers = {}
            def json(self):
                return dict(id=item, site_id='MLB', currency_id='BRL', status='active',
                            price=1500.5, permalink='https://produto.mercadolivre.com.br/' + item)
        return Response()


def main():
    dados = json.loads((ROOT / 'tools/exemplo_comparativo_m0417d.json').read_text())
    dados.pop('_comentario')
    for model, item in zip(dados['modelos'], ('MLB123', 'MLB456')):
        model['ml_id'] = item
    session = FixtureSession()
    client = MercadoLivreClient('token-sintetico', session=session, sleep=lambda _: None,
                                now=lambda: datetime(2026, 10, 30, tzinfo=timezone.utc))
    with patch('requests.sessions.Session.request', side_effect=AssertionError('HTTP real proibido')) as http, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('socket proibido')), \
         patch('mkt_flow_p0.price_collector._salvar_evidencia', side_effect=AssertionError('escrita proibida')) as db:
        rendered = gerar_comparativo(dados['modelos'], coletar_precos=True, cliente_precos=client,
                                    chamar_llm=lambda *a: '<h2>Comparação</h2><p>Fichas documentais.</p>')
        assert 'erro' not in rendered, rendered
        dados['price_history'] = rendered['price_history']
        dados['conteudo_html'] = rendered['html']
        dados['compras'] = {nome: pontos[0]['fonte'] for nome, pontos in dados['price_history'].items()}
        dados['criterios'] = [{'label': 'Preço (fixture)', 'vals': ['R$ 1.500,50', 'R$ 1.500,50'], 'win': 0}]
        result = processar_comparativo(**dados)
        assert result['acao'] == 'dry_run_ok' and result['escreveu'] is False
        assert session.calls == 2
        http.assert_not_called()
        db.assert_not_called()
    print(json.dumps({'tipo': 'fixture_sintetica_sem_cotacao_real',
                      'http_real': 0, 'sqlite_escritas': 0, 'respostas_simuladas': session.calls,
                      'resultado': result}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
