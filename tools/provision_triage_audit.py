"""Provisiona a auditoria de triagem no Turso (apenas DDL idempotente).

A tabela `rss_triage_audit` e os tres triggers de `mkt_flow_p0/triagem_decisoes.py`
nunca foram criados em producao. Sem eles, `triagem_decisoes.decidir()` falha com
SQLITE_AUTH, porque o token de escrita usado pela fila nao tem permissao de DDL.

Este script NAO altera dados: so executa CREATE TABLE/TRIGGER IF NOT EXISTS,
exatamente o mesmo SQL do modulo. Rodar duas vezes nao muda nada.

Token, nesta ordem:
    1) TURSO_AUTH_TOKEN no ambiente (precisa de permissao de schema)
    2) token em cache do Turso CLI (~/.config/turso/settings.json) para o banco
       apontado por TURSO_DATABASE_URL (permissao "rw", inclui DDL)

Uso:
    python tools/provision_triage_audit.py              # previa
    python tools/provision_triage_audit.py --confirmar   # executa
"""
import argparse
import base64
import json
import os
import sys
import urllib.parse

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _candidato in (_RAIZ, os.getcwd()):
    if os.path.isdir(os.path.join(_candidato, "mkt_flow_p0")):
        if _candidato not in sys.path:
            sys.path.insert(0, _candidato)
        break

from mkt_flow_p0 import triagem_decisoes as t  # noqa: E402

ETAPAS = (
    ("tabela de auditoria", t.AUDIT_SCHEMA),
    ("trigger de registro", t.TRIGGER),
    ("trigger imutavel (update)", t.AUDIT_IMMUTABLE_UPDATE),
    ("trigger imutavel (delete)", t.AUDIT_IMMUTABLE_DELETE),
)
SETTINGS_TURSO = os.path.expanduser("~/.config/turso/settings.json")


def _permissao(token):
    """Le o claim 'a' (permissao) do JWT sem expor o segredo."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload)).get("a", "?")
    except Exception:
        return "?"


def token_em_cache(url):
    """Token rw do Turso CLI para o mesmo host, se existir."""
    if not os.path.isfile(SETTINGS_TURSO):
        return None, None
    host = urllib.parse.urlparse(url).hostname
    cache = json.load(open(SETTINGS_TURSO, encoding="utf-8")).get("cache", {})
    for banco in cache.get("database_names", {}).get("data", []):
        if banco.get("Hostname") != host:
            continue
        token = (cache.get("database_token", {}).get(banco["dbId"]) or {}).get("data")
        if token:
            return token, banco.get("Name")
    return None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--confirmar", action="store_true")
    args = ap.parse_args()

    url = os.getenv("TURSO_DATABASE_URL", "").strip()
    if not url:
        raise SystemExit("falta TURSO_DATABASE_URL")

    token = os.getenv("TURSO_AUTH_TOKEN", "").strip()
    origem = "ambiente"
    if not token:
        token, nome = token_em_cache(url)
        origem = f"cache do Turso CLI (banco {nome})" if token else ""
    if not token:
        raise SystemExit("nenhum token disponivel (ambiente ou cache do Turso CLI)")

    os.environ["TURSO_DATABASE_URL"] = url
    os.environ["TURSO_AUTH_TOKEN"] = token

    print(f"banco: {url}")
    print(f"token: {origem} | permissao: {_permissao(token)}")

    if not args.confirmar:
        print("\nprevia (nada foi executado). Etapas:")
        for nome, _sql in ETAPAS:
            print(f"  - {nome}")
        print("\nrode com --confirmar")
        return 0

    from mkt_flow_p0.cloud_db import turso_enabled, turso_execute
    if not turso_enabled():
        raise SystemExit("Turso nao esta habilitado nesta configuracao")

    falhas = 0
    for nome, sql in ETAPAS:
        resultado = turso_execute(sql)
        ok = "rows" in resultado or "affected" in resultado
        print(("OK    " if ok else "FALHA ") + nome)
        if not ok:
            falhas += 1
            print("       " + json.dumps(resultado, ensure_ascii=False)[:200])

    conferencia = turso_execute(
        "SELECT type, name FROM sqlite_master "
        "WHERE name LIKE 'rss_triage%' ORDER BY type, name")
    print("\nobjetos criados:", json.dumps(conferencia.get("rows", conferencia),
                                           ensure_ascii=False))
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
