"""Fila editorial RSS P0. Sem LLM, WordPress, rede nem agendamento próprios."""
import hashlib
import re
import sqlite3
import uuid
import time
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from mkt_flow_p0 import cloud_db
from mkt_flow_p0.prioridade_editorial import avaliar_pauta
from mkt_flow_p0.opportunities import evaluate

DEFAULT_DB = Path(__file__).resolve().parent.parent / "mkt_flow_p0.db"
STATES = frozenset(("DESCOBERTA", "SELECIONADA", "EM_PRODUCAO", "EM_REVISAO",
                    "CONCLUIDA", "REJEITADA", "BLOQUEADA"))
TRANSITIONS = {
    "DESCOBERTA": {"SELECIONADA", "REJEITADA", "BLOQUEADA"},
    "SELECIONADA": {"EM_PRODUCAO", "REJEITADA", "BLOQUEADA"},
    "EM_PRODUCAO": {"EM_REVISAO", "BLOQUEADA", "SELECIONADA"},
    "EM_REVISAO": {"CONCLUIDA", "EM_PRODUCAO", "BLOQUEADA"},
    "CONCLUIDA": set(), "REJEITADA": {"DESCOBERTA"}, "BLOQUEADA": {"DESCOBERTA"},
}
SCHEMA = """CREATE TABLE IF NOT EXISTS rss_pautas (
 id TEXT PRIMARY KEY, fonte TEXT NOT NULL, url TEXT NOT NULL,
 titulo TEXT NOT NULL, titulo_norm TEXT NOT NULL, publicada_em TEXT,
 resumo TEXT, estado TEXT NOT NULL, pontuacao INTEGER NOT NULL,
 motivo TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"""


def _now():
    return datetime.now(timezone.utc).isoformat()


def _normalize(text):
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text.casefold()).strip()


def _url(raw):
    p = urlsplit((raw or "").strip())
    if p.scheme not in ("https", "http") or not p.netloc or p.username or p.password:
        raise ValueError("URL RSS inválida")
    params = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
              if not (k.lower().startswith("utm_") or k.lower() in ("fbclid", "gclid"))]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/") or "/",
                       urlencode(sorted(params)), ""))


def _score(item):
    """Mantém contrato legível 0..100, mas usa agora cinco eixos (1..10)."""
    return avaliar_pauta(item)["pontuacao"]


def _exec(sql, args=(), db_path=None):
    """Falha de Turso nunca é substituída silenciosamente por SQLite."""
    if cloud_db.turso_enabled() and db_path is None:
        result = cloud_db.turso_execute(sql, args)
        if "erro" in result:
            raise RuntimeError("Persistência remota indisponível: " + result["erro"])
        return result.get("rows", []), result.get("affected", 0)
    db = Path(db_path) if db_path is not None else DEFAULT_DB
    with sqlite3.connect(db) as con:
        cur = con.execute(sql, args)
        return cur.fetchall() if cur.description else [], cur.rowcount


NOTAS_SCHEMA = """CREATE TABLE IF NOT EXISTS rss_notas_editoriais (
 pauta_id TEXT PRIMARY KEY, nota INTEGER NOT NULL CHECK(nota BETWEEN 1 AND 10),
 justificativa TEXT NOT NULL, revisada_em TEXT NOT NULL)"""

MUTEX_SCHEMA = """CREATE TABLE IF NOT EXISTS rss_queue_mutex (
 name TEXT PRIMARY KEY, owner TEXT NOT NULL, expires_at INTEGER NOT NULL)"""


def _reserve_writer(db_path=None):
    """Single-writer lease across SQLite/Turso; fail closed on contention."""
    _exec(MUTEX_SCHEMA, db_path=db_path)
    owner = uuid.uuid4().hex
    now = int(time.time())
    _, affected = _exec(
        """INSERT INTO rss_queue_mutex(name, owner, expires_at)
           VALUES ('registration', ?, ?)
           ON CONFLICT(name) DO UPDATE SET owner=excluded.owner,
               expires_at=excluded.expires_at
           WHERE rss_queue_mutex.expires_at < ?""",
        (owner, now + 300, now), db_path)
    if affected != 1:
        raise RuntimeError("Fila RSS ocupada por outro coletor; tente novamente")
    return owner


def _release_writer(owner, db_path=None):
    _exec("DELETE FROM rss_queue_mutex WHERE name='registration' AND owner=?",
          (owner,), db_path)


def init_queue(db_path=None):
    _exec(SCHEMA, db_path=db_path)
    _exec(NOTAS_SCHEMA, db_path=db_path)
    _exec("CREATE INDEX IF NOT EXISTS idx_rss_pautas_estado ON rss_pautas(estado, pontuacao)",
          db_path=db_path)


def registrar(item, db_path=None):
    """Registra descoberta antes de qualquer tentativa de redação. Idempotente."""
    url = _url(item.get("link", ""))
    title = (item.get("titulo") or "").strip()
    if not title:
        raise ValueError("Título RSS obrigatório")
    norm = _normalize(title)
    if not norm:
        raise ValueError("Título RSS vazio")
    init_queue(db_path)
    owner = _reserve_writer(db_path)
    try:
        return _registrar_serializado(item, url, title, norm, db_path)
    finally:
        _release_writer(owner, db_path)


def _registrar_serializado(item, url, title, norm, db_path):
    uid = hashlib.sha256(url.encode()).hexdigest()[:32]
    previous, _ = _exec("SELECT id FROM rss_pautas WHERE id=?", (uid,), db_path)
    if previous:
        return {"id": uid, "novo": False, "motivo": "url_ja_registrada"}
    # Janela curta de similaridade, como o coletor existente.
    recent, _ = _exec("SELECT id, titulo_norm FROM rss_pautas ORDER BY created_at DESC LIMIT 200",
                      db_path=db_path)
    for existing_id, existing_title in recent:
        if SequenceMatcher(None, norm, existing_title).ratio() >= .85:
            return {"id": existing_id, "novo": False, "motivo": "titulo_semelhante"}
    now = _now()
    _, affected = _exec("""INSERT OR IGNORE INTO rss_pautas
        (id, fonte, url, titulo, titulo_norm, publicada_em, resumo, estado,
         pontuacao, motivo, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (uid, item.get("fonte") or "", url, title, norm, item.get("published") or "",
         (item.get("resumo") or "")[:500], "DESCOBERTA", _score(item), "", now, now),
        db_path)
    return {"id": uid, "novo": affected > 0, "estado": "DESCOBERTA",
            "pontuacao": _score(item), "nota": _score(item) // 10,
            "origem_nota": "HEURISTICA_PROVISORIA"}


def mudar_estado(pauta_id, novo_estado, motivo="", db_path=None):
    """Somente transições expressamente autorizadas; não escreve WordPress."""
    if novo_estado not in STATES:
        raise ValueError("Estado inválido")
    init_queue(db_path)
    rows, _ = _exec("SELECT estado FROM rss_pautas WHERE id=?", (pauta_id,), db_path)
    if not rows:
        raise KeyError("Pauta inexistente")
    anterior = rows[0][0]
    if novo_estado not in TRANSITIONS[anterior]:
        raise ValueError("Transição editorial proibida: %s -> %s" % (anterior, novo_estado))
    _, affected = _exec(
        "UPDATE rss_pautas SET estado=?, motivo=?, updated_at=? WHERE id=? AND estado=?",
        (novo_estado, motivo[:500], _now(), pauta_id, anterior), db_path)
    if affected != 1:
        raise RuntimeError("Conflito de transição editorial")
    return {"id": pauta_id, "estado": novo_estado}


def atribuir_nota(pauta_id, nota, justificativa, db_path=None):
    """Correção humana auditável. Nunca muda estado nem libera publicação."""
    if type(nota) is not int or not 1 <= nota <= 10:
        raise ValueError("Nota deve ser inteira entre 1 e 10")
    if not isinstance(justificativa, str) or len(justificativa.strip()) < 10:
        raise ValueError("Justificativa editorial insuficiente")
    init_queue(db_path)
    owner = _reserve_writer(db_path)
    try:
        rows, _ = _exec("SELECT id FROM rss_pautas WHERE id=?", (pauta_id,), db_path)
        if not rows:
            raise KeyError("Pauta inexistente")
        _exec("""INSERT INTO rss_notas_editoriais
                (pauta_id, nota, justificativa, revisada_em)
                VALUES (?,?,?,?)
                ON CONFLICT(pauta_id) DO UPDATE SET
                nota=excluded.nota, justificativa=excluded.justificativa,
                revisada_em=excluded.revisada_em""",
              (pauta_id, nota, justificativa.strip()[:500], _now()), db_path)
        return {"id": pauta_id, "nota": nota, "origem_nota": "REVISAO_EDITORIAL"}
    finally:
        _release_writer(owner, db_path)


def reavaliar_descobertas(limite=100, db_path=None):
    """Migração explícita e idempotente da heurística antiga, sem mexer em status.

    A nota humana, se existente, tem precedência na listagem.
    """
    limite = max(1, min(int(limite), 100))
    init_queue(db_path)
    owner = _reserve_writer(db_path)
    try:
        rows, _ = _exec("""SELECT id, titulo, resumo, publicada_em FROM rss_pautas
                        WHERE estado='DESCOBERTA' ORDER BY created_at DESC LIMIT ?""",
                        (limite,), db_path)
        for pauta_id, titulo, resumo, publicada in rows:
            pontuacao = _score({"titulo": titulo, "resumo": resumo,
                               "published": publicada})
            _exec("UPDATE rss_pautas SET pontuacao=?, updated_at=? WHERE id=? AND estado='DESCOBERTA'",
                  (pontuacao, _now(), pauta_id), db_path)
        return {"reavaliadas": len(rows), "modelo": "nota-editorial/1",
                "wordpress_alterado": False}
    finally:
        _release_writer(owner, db_path)


def listar(estado="DESCOBERTA", limite=20, db_path=None):
    """Prioriza nota humana quando houver; mantém pontuação legada 0..100."""
    if estado not in STATES:
        raise ValueError("Estado inválido")
    init_queue(db_path)
    rows, _ = _exec("""SELECT p.id, p.fonte, p.url, p.titulo, p.estado,
        p.pontuacao, COALESCE(n.nota, MAX(1, MIN(10, CAST((p.pontuacao + 5)/10 AS INTEGER)))) AS nota,
        CASE WHEN n.nota IS NULL THEN 'HEURISTICA_PROVISORIA'
             ELSE 'REVISAO_EDITORIAL' END AS origem_nota,
        p.publicada_em, p.created_at
        FROM rss_pautas p LEFT JOIN rss_notas_editoriais n ON n.pauta_id=p.id
        WHERE p.estado=? ORDER BY nota DESC, p.created_at DESC LIMIT ?""",
        (estado, max(1, min(int(limite), 100))), db_path)
    result = []
    for row in rows:
        item = dict(zip(("id", "fonte", "url", "titulo", "estado", "pontuacao",
                         "nota", "origem_nota", "publicada_em", "created_at"), row))
        # Discovery is preserved. A high heuristic note is never measured demand.
        try:
            item["opportunity"] = evaluate({"title": item["titulo"], "url": item["url"],
                "kind": "noticia", "published_at": item["publicada_em"],
                "event_at": item["publicada_em"], "observed_at": item["created_at"]})
        except ValueError:
            item["opportunity"] = {"status": "REVISAO_PENDENTE",
                "reasons": ["METADADOS_INCOMPLETOS"], "publication_authorized": False}
        result.append(item)
    return result
