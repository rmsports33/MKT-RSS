"""No callbacks through operational entry, including hostile network hooks."""
import socket
from mkt_flow_p0.editorial_pilot import run_operational

def test_operational_entry_denies_callback_without_invoking():
    invoked=[]
    def malicious(_):
        invoked.append(True)
        socket.create_connection(("example.com",443),timeout=1)
    result=run_operational("Fonte de teste",approved_snapshot=True,generate=malicious)
    assert result["status"]=="BLOQUEADO"
    assert result["motivo"]=="callback_legado_desativado"
    assert not invoked and result["escreveu"] is False

def test_operational_entry_requires_approved_snapshot():
    assert run_operational("Fonte")["status"]=="BLOQUEADO"

def test_operational_entry_offline_preview_only():
    r=run_operational("Wi-Fi 7 permite canais de 320 MHz.",approved_snapshot=True)
    assert r["status"]=="PREVIA_DOCUMENTAL"
    assert r["verificacao_factual"]=="NAO_VERIFICADO" and not r["escreveu"]
