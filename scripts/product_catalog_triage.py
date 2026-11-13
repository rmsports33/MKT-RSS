"""Triagem em lote do catálogo, totalmente local e sem chamadas externas.

Entrada: JSON contendo lista de strings ou objetos com campo "produto".
Saída: JSON com classificação conservadora; não grava catálogo ou fila.
"""
import argparse
import json
from pathlib import Path
from mkt_flow_p0.product_catalog import load, match


def triage(items, catalog):
    if not isinstance(items, list):
        raise ValueError("EXPECTED_JSON_LIST")
    output = []
    for item in items:
        name = item if isinstance(item, str) else item.get("produto", "") if isinstance(item, dict) else ""
        if not isinstance(name, str) or not name.strip():
            output.append({"status": "REVIEW", "reason": "INVALID_PRODUCT_NAME"})
            continue
        result = match(name, catalog)
        output.append({"produto": name, **result, "publication_authorized": False})
    return output


def main():
    parser = argparse.ArgumentParser(description="Triagem local de produtos; nenhuma operação remota")
    parser.add_argument("input", type=Path, help="Arquivo JSON de nomes ou objetos")
    parser.add_argument("--output", type=Path, help="Arquivo de resultado opcional")
    args = parser.parse_args()
    items = json.loads(args.input.read_text(encoding="utf-8"))
    result = {"schema": "conexo-product-triage/1", "results": triage(items, load())}
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
