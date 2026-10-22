from unittest.mock import patch

import pipeline_rss as P
from test_pipeline_rss_gate_p0 import ITEM, fluxo_mockado


def test_m0419_gate_bloqueado_nao_envia_ao_wordpress(monkeypatch, tmp_path):
    monkeypatch.delenv("GATE_PUBLICACAO_ENABLED", raising=False)
    with fluxo_mockado(monkeypatch, tmp_path) as mocks:
        with patch("mkt_flow_p0.gate_editorial_pos_ia.validar_saida", return_value={
            "veredito": "BLOQUEADO", "motivos": ["alegacao_de_teste_proprio"]
        }):
            resultado = P.processar_item(ITEM)
    assert resultado["acao"] == "bloqueado"
    assert resultado["motivo"] == "revisao_factual_necessaria"
    mocks.publish.assert_not_called()


def test_m0419_gate_excecao_nao_envia_ao_wordpress(monkeypatch, tmp_path):
    monkeypatch.delenv("GATE_PUBLICACAO_ENABLED", raising=False)
    with fluxo_mockado(monkeypatch, tmp_path) as mocks:
        with patch("mkt_flow_p0.gate_editorial_pos_ia.validar_saida", side_effect=RuntimeError("falha simulada")):
            resultado = P.processar_item(ITEM)
    assert resultado["acao"] == "bloqueado"
    assert resultado["motivo"] == "erro_validacao_editorial"
    mocks.publish.assert_not_called()


def test_m0419_gate_resposta_invalida_nao_envia_ao_wordpress(monkeypatch, tmp_path):
    monkeypatch.delenv("GATE_PUBLICACAO_ENABLED", raising=False)
    with fluxo_mockado(monkeypatch, tmp_path) as mocks:
        with patch("mkt_flow_p0.gate_editorial_pos_ia.validar_saida", return_value=None):
            resultado = P.processar_item(ITEM)
    assert resultado["acao"] == "bloqueado"
    mocks.publish.assert_not_called()


def test_m0419_sem_alertas_apenas_rascunho(monkeypatch, tmp_path):
    monkeypatch.delenv("GATE_PUBLICACAO_ENABLED", raising=False)
    with fluxo_mockado(monkeypatch, tmp_path) as mocks:
        with patch("mkt_flow_p0.gate_editorial_pos_ia.validar_saida", return_value={
            "veredito": "SEM_ALERTAS", "motivos": []
        }):
            resultado = P.processar_item(ITEM)
    assert resultado["acao"] == "publicado_rascunho"
    mocks.publish.assert_called_once()
    assert mocks.publish.call_args.kwargs["status_desejado"] == "draft"
