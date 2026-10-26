"""Isolation boundary tests: no external execution at all."""
import socket
from mkt_flow_p0.editorial_offline_adapter import run_offline, authorize_provider

def test_requires_snapshot():
    assert run_offline("Texto")["status"] == "BLOQUEADO"

def test_does_not_need_or_call_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("network attempt")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    result = run_offline("A fonte registra canais de 320 MHz.", approved_snapshot=True)
    assert result["status"] == "PREVIA_DOCUMENTAL"
    assert result["verificacao_factual"] == "NAO_VERIFICADO"
    assert result["escreveu"] is False
    assert result["auditoria"]["certificacao_factual"] is False

def test_markup_escaped():
    result = run_offline("<script>alert('x')</script>", approved_snapshot=True)
    assert "<script>" not in result["html"]

def test_external_provider_closed_even_if_requested():
    result = authorize_provider(api_key="ignored", approved=True)
    assert result["status"] == "BLOQUEADO"
    assert result["motivo"] == "isolamento_de_rede_nao_certificado"
