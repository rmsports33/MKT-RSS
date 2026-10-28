"""P1 authorization and immutable audit regression tests (offline)."""
import pytest
from mkt_flow_p0.triagem_auth import operador_autorizado
from mkt_flow_p0 import fila_pautas as fila
from mkt_flow_p0.triagem_decisoes import decidir


def test_allowed_github_actor(monkeypatch):
    for k,v in {"GITHUB_ACTOR":"rmsports33","P1_AUTHORIZED_ACTORS":"rmsports33",
                "GITHUB_REPOSITORY":"rmsports33/MKT-RSS",
                "GITHUB_REF":"refs/heads/master",
                "GITHUB_EVENT_NAME":"workflow_dispatch"}.items():
        monkeypatch.setenv(k,v)
    assert operador_autorizado()=="rmsports33"


@pytest.mark.parametrize("override", [
    {"P1_AUTHORIZED_ACTORS":""}, {"P1_AUTHORIZED_ACTORS":"someone-else"},
    {"GITHUB_ACTOR":"intruder"}, {"GITHUB_REPOSITORY":"other/repo"},
    {"GITHUB_REF":"refs/heads/feature"}, {"GITHUB_EVENT_NAME":"pull_request"},
])
def test_denied_contexts(monkeypatch,override):
    values={"GITHUB_ACTOR":"rmsports33","P1_AUTHORIZED_ACTORS":"rmsports33",
            "GITHUB_REPOSITORY":"rmsports33/MKT-RSS",
            "GITHUB_REF":"refs/heads/master",
            "GITHUB_EVENT_NAME":"workflow_dispatch"}
    values.update(override)
    for k,v in values.items():
        monkeypatch.setenv(k,v)
    with pytest.raises(PermissionError):
        operador_autorizado()


def test_audit_update_delete_prohibited(tmp_path):
    db=tmp_path/"triage-audit.db"
    result=fila.registrar({"link":"https://example.org/audit-lock",
                          "titulo":"Pauta sintetica para testar auditoria"},db_path=db)
    audit=decidir(result["id"],"rejeitar","Caso somente teste","editor-teste",
                  confirmado=True,db_path=db)
    with pytest.raises(Exception):
        fila._exec("UPDATE rss_triage_audit SET operador='outro' WHERE event_id=?",
                   (audit["evento"],),db)
    with pytest.raises(Exception):
        fila._exec("DELETE FROM rss_triage_audit WHERE event_id=?",
                   (audit["evento"],),db)
