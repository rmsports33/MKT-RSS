"""Fila editorial RSS P0. Sem LLM, WordPress, rede nem agendamento próprios."""
import hashlib
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from mkt_flow_p0 import cloud_db

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
    """Heurística determinística 0..100; não certifica fatos nem substitui o editor."""
    title = _normalize(item.get("titulo", ""))
    keywords = ("android", "google", "samsung", "iphone", "smartphone", "celular",
                "notebook", "processador", "intel", "amd", "apple", "seguranca",
                "inteligencia artificial", "ia", "windows", "tecnologia")
    matches = sum(1 for k in keywords if k in title)
    return min(100, 30 + min(matches, 3)*15 + (10 if item.get("published") else 0)
               + (5 if len(title) >= 40 else 0))


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


def init_queue(db_path=None):
    _exec(SCHEMA, db_path=db_path)
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
            "pontuacao": _score(item)}


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


def listar(estado="DESCOBERTA", limite=20, db_path=None):
    if estado not in STATES:
        raise ValueError("Estado inválido")
    init_queue(db_path)
    rows, _ = _exec("""SELECT id, fonte, url, titulo, estado, pontuacao
        FROM rss_pautas WHERE estado=? ORDER BY pontuacao DESC, created_at DESC LIMIT ?""",
        (estado, max(1, min(int(limite), 100))), db_path)
    return [dict(zip(("id", "fonte", "url", "titulo", "estado", "pontuacao"), row))
            for row in rows]
