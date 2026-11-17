"""Provisiona a auditoria de triagem no Turso (apenas DDL idempotente).

A tabela `rss_triage_audit` e os tres triggers de `mkt_flow_p0/triagem_decisoes.py`
nunca foram criados em producao. Sem eles, `triagem_decisoes.decidir()` falha com
SQLITE_AUTH, porque o token de escrita usado pela fila nao tem permissao de DDL.

Este script NAO altera dados: so executa CREATE TABLE/TRIGGER IF NOT EXISTS,
exatamente o mesmo SQL do modulo. Rodar duas vezes nao muda nada.

Requer token do Turso com permissao de schema (DDL), via
TURSO_DATABASE_URL + TURSO_AUTH_TOKEN no ambiente.

Uso:
    python tools/provision_triage_audit.py            # mostra o que faria
    python tools/provision_triage_audit.py --confirmar  # executa
"""
import argparse
import json
import os
import sys

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.isdir(os.path.join(_RAIZ, "mkt_flow_p0")) and _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

from mkt_flow_p0 import triagem_decisoes as t  # noqa: E402

ETAPAS = (
    ("tabela de auditoria", t.AUDIT_SCHEMA),
    ("trigger de registro", t.TRIGGER),
    ("trigger imutavel (update)", t.AUDIT_IMMUTABLE_UPDATE),
    ("trigger imutavel (delete)", t.AUDIT_IMMUTABLE_DELETE),
)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--confirmar", action="store_true")
    args = ap.parse_args()

    if not (os.getenv("TURSO_DATABASE_URL", "").strip()
            and os.getenv("TURSO_AUTH_TOKEN", "").strip()):
        raise SystemExit("faltam TURSO_DATABASE_URL e TURSO_AUTH_TOKEN")

    from mkt_flow_p0.cloud_db import turso_enabled, turso_execute
    if not turso_enabled():
        raise SystemExit("Turso nao esta habilitado nesta configuracao")

    if not args.confirmar:
        print("previa (nada foi executado). Etapas:")
        for nome, _sql in ETAPAS:
            print(f"  - {nome}")
        print("\nrode com --confirmar usando um token com permissao de schema")
        return 0

    falhas = 0
    for nome, sql in ETAPAS:
        resultado = turso_execute(sql)
        ok = "rows" in resultado or "affected" in resultado
        print(("OK   " if ok else "FALHA") + f" {nome}")
        if not ok:
            falhas += 1
            print("      " + json.dumps(resultado, ensure_ascii=False)[:200])
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
