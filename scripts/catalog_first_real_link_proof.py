"""Prova pontual de UM vínculo RSS real no Turso já usado pelo MKT-RSS.

Apenas a notícia selecionada é registrada na fila. Não gera texto, rascunho
ou publicação. A etapa de prova deve ser removida após a execução.
"""
import json
import os
from datetime import datetime, timezone
from urllib.parse import urlsplit

from mkt_flow_p0 import cloud_db
from mkt_flow_p0.fila_pautas import registrar, _url
from mkt_flow_p0.product_catalog import load, identify_in_headline
from mkt_flow_p0.product_links import link_pauta
from mkt_flow_p0.rss_ingestor import FEEDS_PADRAO, fetch_feed
from mkt_flow_p0.opportunities import recent

EXPECTED_PRODUCT = "motorola-signature-27"
SOURCE = "gsmarena"
LIMIT = 10

def proof():
    raw = os.getenv("TURSO_DATABASE_URL", "")
    hostname = urlsplit(raw.replace("libsql://", "https://", 1)).hostname or ""
    if (not cloud_db.turso_enabled() or not hostname.endswith(".turso.io")
            or "homolog" in hostname.lower()):
        raise RuntimeError("BLOCKED: authorized production queue Turso credentials unavailable")
    if os.getenv("CONEXO_PRODUCT_LINKS_ENABLED") != "1":
        raise RuntimeError("BLOCKED: links not explicitly enabled")
    feed = fetch_feed(FEEDS_PADRAO[SOURCE], fonte=SOURCE, max_items=LIMIT)
    if feed.get("erro") or not feed.get("itens"):
        raise RuntimeError("BLOCKED: real RSS feed unavailable")
    catalog = load()
    candidates = []
    for item in feed["itens"]:
        classification = identify_in_headline(item.get("titulo", ""), catalog)
        if (classification.get("status") == "CANDIDATE_MATCH"
                and classification.get("product_id") == EXPECTED_PRODUCT
                and recent(item.get("published"), datetime.now(timezone.utc), 168)):
            candidates.append(item)
    if len(candidates) != 1:
        raise RuntimeError("BLOCKED: expected one recent real RSS item for approved product")
    item = candidates[0]
    # This invokes the exact existing RSS queue persistence function.
    receipt = registrar(item)
    pauta_id = receipt.get("id")
    if not isinstance(pauta_id, str) or not pauta_id:
        raise RuntimeError("BLOCKED: RSS queue receipt did not confirm pauta ID")
    linked = link_pauta(EXPECTED_PRODUCT, pauta_id, item["link"])
    if linked.get("status") != "LINKED" or linked.get("publication_authorized") is not False:
        raise RuntimeError("BLOCKED: product link was not confirmed")
    # Authenticated readback of BOTH queue item and association.
    sql = """SELECT p.id, p.url, p.estado, l.wp_post_id, l.wp_status
             FROM rss_pautas p JOIN rss_product_links l ON l.pauta_id=p.id
             WHERE p.id=? AND l.product_id=?"""
    result = cloud_db.turso_execute(sql, (pauta_id, EXPECTED_PRODUCT))
    if result.get("erro") or len(result.get("rows", [])) != 1:
        raise RuntimeError("BLOCKED: Turso authenticated readback not confirmed")
    row = result["rows"][0]
    if (row[0] != pauta_id or row[1] != _url(item["link"])
            or row[2] not in ("DESCOBERTA", "SELECIONADA", "EM_PRODUCAO",
                             "EM_REVISAO", "CONCLUIDA", "REJEITADA", "BLOQUEADA")
            or row[3] is not None or row[4] is not None):
        raise RuntimeError("BLOCKED: Turso readback inconsistent")
    # One additional read-only check confirms the unique association.
    count = cloud_db.turso_execute(
        "SELECT COUNT(*) FROM rss_product_links WHERE product_id=? AND pauta_id=?",
        (EXPECTED_PRODUCT, pauta_id))
    if count.get("erro") or count.get("rows") != [[1]]:
        raise RuntimeError("BLOCKED: idempotent unique product-pauta link not confirmed")
    return {
        "result": "PASS",
        "mode": "ONE_REAL_RSS_PRODUCT_LINK",
        "source": SOURCE,
        "product_id": EXPECTED_PRODUCT,
        "pauta_id": pauta_id,
        "source_url": _url(item["link"]),
        "queue_new": receipt.get("novo"),
        "queue_state": row[2],
        "authenticated_turso_readback": True,
        "link_count": 1,
        "wp_post_id": None,
        "wordpress_modified": False,
        "publication_authorized": False,
    }

def main():
    try:
        outcome = proof()
    except (RuntimeError, ValueError, KeyError, TypeError):
        raise SystemExit("BLOCKED: real operational link proof failed; inspect safe checks") from None
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
