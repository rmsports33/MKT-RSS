"""CLI somente leitura para exportar candidatos RSS ao Conexo OS.

Exemplo: python -m mkt_flow_p0.conexo_discovery_export --limite 20 > candidatos.json
A transferencia do arquivo ao consumidor e supervisionada, nao automatizada.
"""
import argparse
import json
import sys

from mkt_flow_p0.conexo_discovery_adapter import exportar_candidatos


def main(argv=None):
    parser = argparse.ArgumentParser(description="Exportar candidatos RSS sem publicacao")
    parser.add_argument("--limite", type=int, default=20)
    parser.add_argument("--db", help="SQLite local de homologacao; omitir para configuracao existente")
    args = parser.parse_args(argv)
    try:
        pacote = exportar_candidatos(args.limite, db_path=args.db)
    except (ValueError, RuntimeError, OSError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(pacote, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
