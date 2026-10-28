"""P1: consulta exclusivamente de leitura da fila editorial RSS.

Sem escrita de estado, redação, LLM ou WordPress.
"""
import argparse
import json
import os
from urllib.parse import urlsplit

from mkt_flow_p0.fila_pautas import listar

HOST_HOMOLOG = "mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io"


def consultar_guard():
    url = os.getenv("TURSO_DATABASE_URL", "")
    token = os.getenv("TURSO_AUTH_TOKEN", "")
    p = urlsplit(url)
    if (p.scheme != "libsql" or p.hostname != HOST_HOMOLOG
            or p.username or p.password or p.port or p.path not in ("", "/")):
        raise RuntimeError("P1 bloqueada: usar somente Turso de homologacao")
    if not token.strip():
        raise RuntimeError("P1 bloqueada: token de homologacao ausente")


def consultar(limite=20, *, exigir_homolog=False):
    if not 1 <= limite <= 20:
        raise ValueError("Limite P1 deve estar entre 1 e 20")
    if exigir_homolog:
        consultar_guard()
    pautas = listar(estado="DESCOBERTA", limite=limite)
    return {
        "modo": "somente_leitura",
        "estado": "DESCOBERTA",
        "total": len(pautas),
        "pontuacao": "heuristica; nao comprova veracidade, relevancia ou aprovacao editorial",
        "pautas": pautas,
    }


def main():
    ap = argparse.ArgumentParser(description="P1: listagem editorial somente leitura")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--homolog", action="store_true",
                    help="Exige credenciais Turso restritas a mkt-rss-homolog")
    ap.add_argument("--acao", choices=("selecionar", "rejeitar"))
    ap.add_argument("--pauta-id")
    ap.add_argument("--justificativa")
    ap.add_argument("--operador")
    ap.add_argument("--confirm", action="store_true")
    ap.add_argument("--historico-id")
    args = ap.parse_args()
    try:
        if args.acao or args.historico_id:
            if not args.homolog:
                raise ValueError("Decisoes e historico exigem --homolog")
            consultar_guard()
            from mkt_flow_p0.triagem_decisoes import decidir, historico
            if args.acao:
                raise RuntimeError("Decisao bloqueada: identidade e autorizacao autenticadas ainda nao integradas")
            else:
                result = {"historico": historico(args.historico_id)}
        else:
            result = consultar(args.limit, exigir_homolog=args.homolog)
    except (ValueError, RuntimeError, OSError) as exc:
        print(json.dumps({"erro": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
