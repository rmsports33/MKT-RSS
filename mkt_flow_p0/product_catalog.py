"""Catálogo editorial de referência. Não altera Turso, WordPress nem Gate."""
import json
import re
import unicodedata
from pathlib import Path

DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "mkt-flow-escrita/pautas/catalogo-produtos.json"

def normalize(value):
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()

def load(path=DEFAULT_CATALOG):
    catalog = json.loads(Path(path).read_text(encoding="utf-8"))
    if catalog.get("schema") != "conexo-product-catalog/1":
        raise ValueError("CATALOG_SCHEMA_INVALID")
    seen = set()
    for product in catalog["products"]:
        if product["id"] in seen:
            raise ValueError("DUPLICATE_CANONICAL_ID")
        seen.add(product["id"])
    return catalog

def match(name, catalog):
    """Exact normalized alias match. Ambiguity never auto-merges records."""
    target = normalize(name)
    found = []
    for product in catalog["products"]:
        names = product["aliases"] + [product["brand"] + " " + product["model"]]
        if target in {normalize(x) for x in names}:
            found.append(product)
    if len(found) > 1:
        return {"status": "REVIEW", "reason": "AMBIGUOUS_ALIAS"}
    if found:
        return {"status": "EXISTS", "product_id": found[0]["id"]}
    return {"status": "NEW_CANDIDATE", "requires_review": True}

def register_candidate(catalog, product):
    """Return a new catalog in memory; caller must explicitly persist it."""
    result = match(product["brand"] + " " + product["model"], catalog)
    if result["status"] != "NEW_CANDIDATE":
        return catalog, result
    if any(p["id"] == product["id"] for p in catalog["products"]):
        return catalog, {"status": "REVIEW", "reason": "DUPLICATE_CANONICAL_ID"}
    updated = dict(catalog)
    updated["products"] = catalog["products"] + [product]
    return updated, {"status": "ADDED_IN_MEMORY", "product_id": product["id"],
                     "requires_review": True, "publication_authorized": False}
