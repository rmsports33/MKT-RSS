"""Registra UMA decisao de triagem (selecionar/rejeitar) com auditoria.

Mecanismo adaptado do desenho original (workflow do GitHub Actions com allowlist
de ator + aprovacao de environment) para execucao local/servidor, porque a
politica do projeto despriorizou Actions como executor.

Diferencas praticas:

| Desenho original (Actions)      | Adaptacao aqui                          |
|---------------------------------|-----------------------------------------|
| identidade = GITHUB_ACTOR       | identidade = usuario autenticado do SO  |
| aprovacao de environment        | `--confirmar` explicito, uma pauta      |
| allowlist P1_AUTHORIZED_ACTORS  | allowlist P1_AUTHORIZED_OPERATORS       |
| grava no Turso via runner       | grava no Turso via token do ambiente    |

Continua fail-closed: sem tabela/trigger de auditoria, sem confirmacao, com
identidade fora da allowlist ou com pauta que nao esteja em DESCOBERTA, nada e
gravado.

Uso:
    python tools/triagem_decidir.py --listar
    python tools/triagem_decidir.py --pauta-id <32 hex> --acao selecionar \
        --justificativa "motivo curto" --confirmar

Variaveis: TURSO_DATABASE_URL, TURSO_AUTH_TOKEN, P1_AUTHORIZED_OPERATORS (opcional)
"""
import argparse
import getpass
import json
import os
import re
import sys

for _c in (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), os.getcwd()):
    if os.path.isdir(os.path.join(_c, "mkt_flow_p0")):
        if _c not in sys.path:
            sys.path.insert(0, _c)
        break

from mkt_flow_p0 import triagem_decisoes  # noqa: E402
from mkt_flow_p0.cloud_db import turso_enabled, turso_execute  # noqa: E402


def exigir_turso():
    if not turso_enabled():
        raise SystemExit("TURSO_DATABASE_URL/TURSO_AUTH_TOKEN ausentes; nada gravado")


def auditoria_pronta():
    """Falha fechado se a auditoria nao estiver provisionada."""
    r = turso_execute("SELECT type, name FROM sqlite_master WHERE name LIKE 'rss_triage%'")
    objetos = r.get("rows") or []
    tipos = {linha[0] for linha in objetos}
    if "table" not in tipos or "trigger" not in tipos:
        raise SystemExit(
            "auditoria nao provisionada (tabela/trigger ausentes). "
            "Rode tools/provision_triage_audit.py --confirmar antes.")
    return len(objetos)


def identidade():
    """Identidade do operador vem do sistema, nao de texto livre."""
    usuario = getpass.getuser().strip()
    permitidos = [x.strip().lower()
                  for x in os.getenv("P1_AUTHORIZED_OPERATORS", "").split(",") if x.strip()]
    if permitidos and usuario.lower() not in permitidos:
        raise SystemExit(f"operador '{usuario}' fora da allowlist P1; nada gravado")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,60}", usuario):
        raise SystemExit("identidade do sistema nao serve como operador; nada gravado")
    return usuario


def listar(limite=30):
    r = turso_execute("SELECT id, pontuacao, substr(titulo,1,70) FROM rss_pautas "
                      f"WHERE estado='DESCOBERTA' ORDER BY pontuacao DESC, created_at DESC "
                      f"LIMIT {int(limite)}")
    linhas = r.get("rows") or []
    print(f"pautas em DESCOBERTA (mostrando {len(linhas)}):")
    for pauta_id, pontuacao, titulo in linhas:
        print(f"  {pauta_id}  [{pontuacao}]  {titulo}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--pauta-id")
    ap.add_argument("--acao", choices=("selecionar", "rejeitar"))
    ap.add_argument("--justificativa", default="")
    ap.add_argument("--confirmar", action="store_true")
    args = ap.parse_args()

    exigir_turso()

    if args.listar:
        return listar()

    if not (args.pauta_id and args.acao and args.justificativa):
        raise SystemExit("use --pauta-id, --acao e --justificativa (ou --listar)")
    if not args.confirmar:
        raise SystemExit("sem --confirmar nada e gravado (falha fechada)")

    objetos = auditoria_pronta()
    operador = identidade()

    resultado = triagem_decisoes.decidir(
        args.pauta_id, args.acao, args.justificativa, operador, confirmado=True)

    print(f"auditoria provisionada ({objetos} objetos) | operador: {operador}")
    print(f"pauta {resultado['pauta_id']}: {resultado['anterior']} -> {resultado['posterior']}")
    print(f"evento: {resultado['evento']} | em: {resultado['ocorrido_em']}")

    conferencia = turso_execute(
        "SELECT estado, substr(motivo,1,80) FROM rss_pautas WHERE id=?", (args.pauta_id,))
    print("readback:", json.dumps(conferencia.get("rows"), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
