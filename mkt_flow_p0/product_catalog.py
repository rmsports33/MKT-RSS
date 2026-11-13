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

# Sufixos comerciais que distinguem modelos. Não inferir que o modelo base
# corresponde à edição Pro/Plus/Ultra mencionada imediatamente após o nome.
VARIANT_SUFFIXES = frozenset({"pro", "max", "plus", "ultra", "mini", "lite", "air"})

def identify_in_headline(headline, catalog):
    """Classify an RSS headline without modifying the RSS queue or product catalog.

    Exact alias phrases only. Multiple candidates require editorial review.
    """
    title = normalize(headline)
    found = []
    for product in catalog["products"]:
        aliases = product["aliases"] + [product["brand"] + " " + product["model"]]
        for alias in aliases:
            phrase = normalize(alias)
            if phrase:
                hit = re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", title)
                if hit:
                    tail = title[hit.end():].strip().split(" ", 1)[0]
                    if tail in VARIANT_SUFFIXES:
                        continue  # ex.: iPhone 17 Pro != iPhone 17
                    found.append(product["id"])
                    break
    unique = sorted(set(found))
    if not unique:
        return {"status": "NO_MATCH", "publication_authorized": False}
    if len(unique) != 1:
        return {"status": "REVIEW", "candidate_ids": unique, "publication_authorized": False}
    return {"status": "CANDIDATE_MATCH", "product_id": unique[0],
            "requires_editorial_confirmation": True, "publication_authorized": False}
