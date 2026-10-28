"""Offline P1 audit invariants, isolated SQLite only."""
import pytest
from mkt_flow_p0 import fila_pautas
from mkt_flow_p0.triagem_decisoes import decidir, historico


@pytest.fixture
def pauta(tmp_path):
    db = tmp_path / "triage.db"
    link = "https://example.org/p1"
    item = {"link": link, "titulo": "Pauta de teste sobre Android", "fonte": "teste"}
    reg = fila_pautas.registrar(item, db_path=db)
    return db, reg["id"]


def test_selecao_auditoria_persistente(pauta):
    db, uid = pauta
    event = decidir(uid, "selecionar", "Fonte confirmada", "editor-01",
                   confirmado=True, db_path=db)
    assert event["anterior"] == "DESCOBERTA"
    assert event["posterior"] == "SELECIONADA"
    assert event["justificativa"] == "Fonte confirmada"
    assert historico(uid, db_path=db) == [event]
    rows, _ = fila_pautas._exec("SELECT estado FROM rss_pautas WHERE id=?", (uid,), db)
    assert rows[0][0] == "SELECIONADA"


def test_rejeicao_persistente(pauta):
    db, uid = pauta
    event = decidir(uid, "rejeitar", "Tema irrelevante", "editor-01",
                   confirmado=True, db_path=db)
    assert event["posterior"] == "REJEITADA"
    assert len(historico(uid, db_path=db)) == 1


@pytest.mark.parametrize("action,why,actor,confirmed", [
    ("selecionar", "Motivo bom", "editor-01", False),
    ("selecionar", "", "editor-01", True),
    ("selecionar", "Motivo bom", "", True),
    ("aprovar", "Motivo bom", "editor-01", True),
])
def test_invalid_inputs_no_change(pauta, action, why, actor, confirmed):
    db, uid = pauta
    with pytest.raises(ValueError):
        decidir(uid, action, why, actor, confirmado=confirmed, db_path=db)
    rows, _ = fila_pautas._exec("SELECT estado FROM rss_pautas WHERE id=?", (uid,), db)
    assert rows[0][0] == "DESCOBERTA"


def test_repeat_or_missing_id_fail_closed(pauta):
    db, uid = pauta
    with pytest.raises(RuntimeError):
        decidir("a"*32, "rejeitar", "Sem pauta", "editor-01",
               confirmado=True, db_path=db)
    decidir(uid, "selecionar", "Pauta selecionada", "editor-01",
           confirmado=True, db_path=db)
    with pytest.raises(RuntimeError):
        decidir(uid, "rejeitar", "Tentativa repetida", "editor-01",
               confirmado=True, db_path=db)
    assert len(historico(uid, db_path=db)) == 1


def test_audit_fail_rollback(monkeypatch, pauta):
    db, uid = pauta
    # Force audit insertion to fail using a constraint trigger; UPDATE must rollback.
    fila_pautas._exec("""CREATE TRIGGER block_audit BEFORE INSERT ON rss_triage_audit
       BEGIN SELECT RAISE(ABORT, 'audit blocked'); END""", db_path=db) if False else None
    from mkt_flow_p0.triagem_decisoes import preparar
    preparar(db)
    fila_pautas._exec("""CREATE TRIGGER block_audit BEFORE INSERT ON rss_triage_audit
       BEGIN SELECT RAISE(ABORT, 'audit blocked'); END""", db_path=db)
    with pytest.raises(Exception):
        decidir(uid, "selecionar", "Motivo auditado", "editor-01",
               confirmado=True, db_path=db)
    rows, _ = fila_pautas._exec("SELECT estado FROM rss_pautas WHERE id=?", (uid,), db)
    assert rows[0][0] == "DESCOBERTA"
