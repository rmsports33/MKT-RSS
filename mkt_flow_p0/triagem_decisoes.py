"""P1: decisão editorial individual com auditoria atômica via trigger SQL.

A inserção no histórico ocorre na mesma instrução UPDATE; sem WordPress.
"""
import json
import re
import uuid

from mkt_flow_p0 import fila_pautas as fila

AUDIT_SCHEMA = """CREATE TABLE IF NOT EXISTS rss_triage_audit (
 event_id TEXT PRIMARY KEY, pauta_id TEXT NOT NULL,
 anterior TEXT NOT NULL, posterior TEXT NOT NULL,
 operador TEXT NOT NULL, justificativa TEXT NOT NULL,
 ocorrido_em TEXT NOT NULL
)"""
TRIGGER = """CREATE TRIGGER IF NOT EXISTS rss_triage_audit_after_update
AFTER UPDATE OF estado ON rss_pautas
WHEN OLD.estado = 'DESCOBERTA'
 AND NEW.estado IN ('SELECIONADA','REJEITADA')
 AND json_valid(NEW.motivo)
 AND json_extract(NEW.motivo,'$.tipo') = 'triagem_p1'
BEGIN
 INSERT INTO rss_triage_audit (
  event_id, pauta_id, anterior, posterior, operador, justificativa, ocorrido_em
 ) VALUES (
  json_extract(NEW.motivo,'$.evento'), NEW.id, OLD.estado, NEW.estado,
  json_extract(NEW.motivo,'$.operador'),
  json_extract(NEW.motivo,'$.justificativa'), NEW.updated_at
 );
END"""


AUDIT_IMMUTABLE_UPDATE = """CREATE TRIGGER IF NOT EXISTS rss_triage_audit_no_update
BEFORE UPDATE ON rss_triage_audit
BEGIN SELECT RAISE(ABORT, 'audit immutable'); END"""
AUDIT_IMMUTABLE_DELETE = """CREATE TRIGGER IF NOT EXISTS rss_triage_audit_no_delete
BEFORE DELETE ON rss_triage_audit
BEGIN SELECT RAISE(ABORT, 'audit immutable'); END"""


def preparar(db_path=None):
    fila.init_queue(db_path)
    fila._exec(AUDIT_SCHEMA, db_path=db_path)
    fila._exec(TRIGGER, db_path=db_path)
    fila._exec(AUDIT_IMMUTABLE_UPDATE, db_path=db_path)
    fila._exec(AUDIT_IMMUTABLE_DELETE, db_path=db_path)


def decidir(pauta_id, acao, justificativa, operador, *, confirmado=False, db_path=None):
    """Só muda DESCOBERTA com aprovação explícita; histórico na mesma transação."""
    if not confirmado:
        raise ValueError("Confirmação humana obrigatória (--confirm)")
    if acao not in ("selecionar", "rejeitar"):
        raise ValueError("Ação inválida")
    if not re.fullmatch(r"[0-9a-f]{32}", pauta_id or ""):
        raise ValueError("ID de pauta inválido")
    justificativa = (justificativa or "").strip()
    operador = (operador or "").strip()
    if not 3 <= len(justificativa) <= 240:
        raise ValueError("Justificativa obrigatória (3 a 240 caracteres)")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,60}", operador):
        raise ValueError("Identificação do operador inválida")
    posterior = "SELECIONADA" if acao == "selecionar" else "REJEITADA"
    evento = uuid.uuid4().hex
    motivo = json.dumps({"tipo": "triagem_p1", "evento": evento, "operador": operador,
                         "justificativa": justificativa}, ensure_ascii=False)
    preparar(db_path)
    _, affected = fila._exec(
        """UPDATE rss_pautas SET estado=?, motivo=?, updated_at=?
           WHERE id=? AND estado='DESCOBERTA'""",
        (posterior, motivo, fila._now(), pauta_id), db_path)
    if affected != 1:
        raise RuntimeError("Pauta inexistente, já decidida ou conflito de estado")
    rows, _ = fila._exec(
        """SELECT event_id, pauta_id, anterior, posterior, operador,
                  justificativa, ocorrido_em FROM rss_triage_audit
           WHERE event_id=?""", (evento,), db_path)
    if len(rows) != 1:
        raise RuntimeError("Auditoria ausente após decisão: operação requer investigação")
    return dict(zip(("evento","pauta_id","anterior","posterior","operador",
                     "justificativa","ocorrido_em"), rows[0]))


def historico(pauta_id, *, db_path=None):
    preparar(db_path)
    rows, _ = fila._exec(
        """SELECT event_id, pauta_id, anterior, posterior, operador,
                  justificativa, ocorrido_em FROM rss_triage_audit
           WHERE pauta_id=? ORDER BY ocorrido_em DESC""", (pauta_id,), db_path)
    return [dict(zip(("evento","pauta_id","anterior","posterior","operador",
                      "justificativa","ocorrido_em"), row)) for row in rows]
