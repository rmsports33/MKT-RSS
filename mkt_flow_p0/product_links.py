"""Vínculos operacionais produto↔pauta↔rascunho, usando o banco da fila.

O reconhecimento não autoriza publicação. Nenhuma consulta WordPress aqui.
As rotinas requerem a pauta existente e a mesma URL canônica; falha fechada
quando a fila é indisponível. Sem segundo banco/executor.
"""
import os
from mkt_flow_p0.fila_pautas import _exec, _url
from mkt_flow_p0 import cloud_db

SCHEMA = """CREATE TABLE IF NOT EXISTS rss_product_links (
 product_id TEXT NOT NULL,
 pauta_id TEXT NOT NULL,
 source_url TEXT NOT NULL,
 wp_post_id INTEGER,
 wp_status TEXT,
 wp_link TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY (product_id, pauta_id),
 FOREIGN KEY (pauta_id) REFERENCES rss_pautas(id))"""

def _ensure(db_path=None):
    if os.getenv("CONEXO_RSS_SCHEMA_PREEXISTS") == "1":
        _exec("SELECT product_id FROM rss_product_links LIMIT 0", db_path=db_path)
        return
    _exec(SCHEMA, db_path=db_path)

def _require_persistence(db_path):
    if db_path is None and not cloud_db.turso_enabled():
        raise RuntimeError("PRODUCT_LINK_CLOUD_CREDENTIALS_MISSING")

def link_pauta(product_id, pauta_id, source_url, db_path=None):
    """Associa apenas correspondência conservadora com pauta/URL verificadas."""
    if not isinstance(product_id, str) or not product_id or not isinstance(pauta_id, str) or not pauta_id:
        raise ValueError("PRODUCT_LINK_INVALID")
    canonical = _url(source_url)
    _require_persistence(db_path)
    rows, _ = _exec("SELECT url FROM rss_pautas WHERE id=?", (pauta_id,), db_path)
    if len(rows) != 1 or rows[0][0] != canonical:
        return {"status": "SKIPPED_UNVERIFIED_QUEUE", "publication_authorized": False}
    _ensure(db_path)
    _exec("""INSERT OR IGNORE INTO rss_product_links(product_id,pauta_id,source_url)
             VALUES (?,?,?)""", (product_id, pauta_id, canonical), db_path)
    # INSERT OR IGNORE pode não gravar: nunca declarar sucesso sem readback.
    observed, _ = _exec(
        "SELECT source_url FROM rss_product_links WHERE product_id=? AND pauta_id=?",
        (product_id, pauta_id), db_path)
    if len(observed) != 1 or observed[0][0] != canonical:
        return {"status": "LINK_READBACK_PENDING", "publication_authorized": False}
    return {"status": "LINKED", "product_id": product_id,
            "pauta_id": pauta_id, "publication_authorized": False}

def link_verified_draft(source_url, staged, db_path=None):
    """Só aceita recibo real do WordPress depois do readback no adaptador.

    A pauta deve existir e já ter vínculo validado pelo reconhecimento RSS.
    Nunca altera artigo ou Gate nem permite publicar/agendar.
    """
    if (not isinstance(staged, dict) or staged.get("acao") != "publicado_rascunho"
            or staged.get("status") != "draft" or type(staged.get("post_id")) is not int
            or staged["post_id"] <= 0):
        return {"status": "SKIPPED_NOT_VERIFIED_DRAFT", "publication_authorized": False}
    canonical = _url(source_url)
    _require_persistence(db_path)
    _ensure(db_path)
    rows, _ = _exec(
        """SELECT l.product_id, l.pauta_id FROM rss_product_links l
           JOIN rss_pautas p ON p.id=l.pauta_id
           WHERE l.source_url=? AND p.url=?""", (canonical, canonical), db_path)
    if not rows:
        return {"status": "SKIPPED_NO_QUEUE_LINK", "publication_authorized": False}
    post_id = staged["post_id"]
    link = staged.get("wp_link")
    if link is not None and (not isinstance(link, str) or not link.startswith("https://")):
        return {"status": "SKIPPED_INVALID_WP_LINK", "publication_authorized": False}
    # O mesmo post não pode ser silenciosamente trocado por outro, inclusive em rerun.
    for product_id, pauta_id in rows:
        current, _ = _exec(
            "SELECT wp_post_id FROM rss_product_links WHERE product_id=? AND pauta_id=?",
            (product_id, pauta_id), db_path)
        if not current or (current[0][0] is not None and int(current[0][0]) != post_id):
            return {"status": "REVIEW_WP_POST_CONFLICT", "publication_authorized": False}
    for product_id, pauta_id in rows:
        _exec(
            """UPDATE rss_product_links SET wp_post_id=?, wp_status='draft',
               wp_link=?, updated_at=CURRENT_TIMESTAMP
               WHERE product_id=? AND pauta_id=? AND (wp_post_id IS NULL OR wp_post_id=?)""",
            (post_id, link, product_id, pauta_id, post_id), db_path)
    # Evidência posterior independente do UPDATE: o recibo WP sozinho
    # não comprova que o vínculo foi realmente persistido no Turso.
    evidence = verify_draft_link(canonical, post_id, db_path=db_path)
    if evidence["status"] != "DRAFT_LINK_CONFIRMED":
        return evidence
    return {"status": "DRAFT_LINKED", "count": evidence["count"],
            "post_id": post_id, "publication_authorized": False}


def verify_draft_link(source_url, post_id, db_path=None):
    """Readback do vínculo no banco da fila; não consulta nem aprova WordPress."""
    if type(post_id) is not int or post_id <= 0:
        raise ValueError("WP_POST_ID_INVALID")
    _require_persistence(db_path)
    canonical = _url(source_url)
    rows, _ = _exec(
        """SELECT l.wp_post_id, l.wp_status FROM rss_product_links l
           JOIN rss_pautas p ON p.id=l.pauta_id
           WHERE l.source_url=? AND p.url=?""", (canonical, canonical), db_path)
    if not rows:
        return {"status": "SKIPPED_NO_QUEUE_LINK", "publication_authorized": False}
    if any(str(row[0]) != str(post_id) or row[1] != "draft" for row in rows):
        return {"status": "LINK_READBACK_PENDING", "publication_authorized": False}
    return {"status": "DRAFT_LINK_CONFIRMED", "count": len(rows),
            "post_id": post_id, "publication_authorized": False}


def list_links(product_id, db_path=None):
    if not isinstance(product_id, str) or not product_id:
        raise ValueError("PRODUCT_ID_INVALID")
    _require_persistence(db_path)
    _ensure(db_path)
    rows, _ = _exec(
        """SELECT pauta_id, wp_post_id, wp_status FROM rss_product_links
           WHERE product_id=? ORDER BY pauta_id""", (product_id,), db_path)
    return [{"pauta_id": row[0], "wp_post_id": row[1], "wp_status": row[2],
             "publication_authorized": False} for row in rows]
