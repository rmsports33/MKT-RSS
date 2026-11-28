"""Registra um artigo aprovado como padrão de estrutura por gênero.

Uso (após a nota humana no Gate e a conferência dos fatos):
  python tools/atualizar_golden_set.py --artigo artigo.md --receita quality-receipt.json \
      --nota-humana 88 --genero analise --id 9925 --aprovado --fatos-conferidos
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mkt_flow_p0.editorial_golden_set import registrar, resumo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artigo", type=Path, required=True)
    ap.add_argument("--receita", type=Path, required=True)
    ap.add_argument("--nota-humana", type=int, required=True)
    ap.add_argument("--genero", required=True)
    ap.add_argument("--id", required=True)
    ap.add_argument("--aprovado", action="store_true")
    ap.add_argument("--fatos-conferidos", action="store_true")
    args = ap.parse_args()
    texto = args.artigo.read_text(encoding="utf-8")
    receita = json.loads(args.receita.read_text(encoding="utf-8"))
    try:
        item = registrar(texto, genero=args.genero, nota_humana=args.nota_humana,
                         nota_assistida=int(receita.get("nota_assistida") or 0),
                         artigo_id=args.id, aprovado_por_humano=args.aprovado,
                         fato_conferido=args.fatos_conferidos)
    except ValueError as exc:
        print(json.dumps({"status": "BLOQUEADO", "motivo": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "REGISTRADO", "artigo_id": item["artigo_id"],
                      "genero": item["genero"], "nota_humana": item["nota_humana"],
                      "resumo": resumo()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
