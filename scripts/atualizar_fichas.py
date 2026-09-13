#!/usr/bin/env python3
"""
scripts/atualizar_fichas.py — entrada única de fichas verificadas.

Uso:
  python scripts/atualizar_fichas.py --modelo "Galaxy A54" --categoria celular \
    --fonte "fabricante Samsung (samsung.com/br)" --specs '{"tela.polegadas":"6.4"}'

  python scripts/atualizar_fichas.py --modelo "Redmi Note 13" --arquivo ficha.json
  python scripts/atualizar_fichas.py --listar
  python scripts/atualizar_fichas.py --modelo "Galaxy A54" --remover

Sem --specs/--arquivo, tenta buscar via cache/curated e orienta o que falta.
Nunca inventa specs: sem fonte, registra "— não informado" no gerador.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CURATED = ROOT / "redator-artigo-blogs" / "data" / "curated_specs.json"
if str(ROOT / "redator-artigo-blogs") not in sys.path:
    sys.path.insert(0, str(ROOT / "redator-artigo-blogs"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _carregar() -> list:
    if not CURATED.exists():
        return []
    try:
        data = json.loads(CURATED.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _salvar(lista: list):
    CURATED.parent.mkdir(parents=True, exist_ok=True)
    CURATED.write_text(json.dumps(lista, ensure_ascii=False, indent=2), encoding="utf-8")


def listar():
    for item in _carregar():
        print(f"- {item.get('modelo')} ({item.get('categoria','geral')}) — {item.get('fonte','')} — {len(item.get('specs',{}))} specs")


def salvar_ficha(modelo: str, categoria: str, specs: dict, fonte: str):
    modelo = (modelo or "").strip()
    if not modelo:
        print(json.dumps({"erro": "modelo é obrigatório"}))
        sys.exit(2)
    if not isinstance(specs, dict) or not specs:
        print(json.dumps({"erro": "specs vazio — forneça --specs ou --arquivo"}))
        sys.exit(2)
    lista = _carregar()
    idx = next((i for i, it in enumerate(lista) if str(it.get("modelo","")).lower() == modelo.lower()), None)
    entrada = {"modelo": modelo, "categoria": (categoria or "geral").lower(), "specs": specs, "fonte": fonte or "curated"}
    if idx is not None:
        lista[idx] = entrada
        acao = "atualizada"
    else:
        lista.append(entrada)
        acao = "criada"
    _salvar(lista)
    print(json.dumps({"acao": acao, "modelo": modelo, "specs": len(specs), "fonte": entrada["fonte"]}, ensure_ascii=False))


def remover(modelo: str):
    lista = _carregar()
    nova = [it for it in lista if str(it.get("modelo","")).lower() != modelo.lower()]
    if len(nova) == len(lista):
        print(json.dumps({"erro": f"modelo não encontrado: {modelo}"}))
        sys.exit(3)
    _salvar(nova)
    print(json.dumps({"acao": "removida", "modelo": modelo}))


def main():
    ap = argparse.ArgumentParser(description="Gerencia curated_specs.json (fichas verificadas)")
    ap.add_argument("--modelo", default="")
    ap.add_argument("--categoria", default="geral")
    ap.add_argument("--fonte", default="")
    ap.add_argument("--specs", default="", help='JSON dict, ex: \'{"tela.hz":"120"}\'')
    ap.add_argument("--arquivo", default="", help="arquivo JSON com {specs, fonte} ou dict direto")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--remover", action="store_true")
    args = ap.parse_args()

    if args.listar:
        listar()
        return
    if args.remover:
        if not args.modelo:
            ap.error("--modelo é obrigatório com --remover")
        remover(args.modelo)
        return
    if not args.modelo:
        ap.error("--modelo é obrigatório (ou use --listar)")

    specs = {}
    fonte = args.fonte or ""
    if args.arquivo:
        try:
            data = json.loads(Path(args.arquivo).read_text(encoding="utf-8"))
            if isinstance(data, dict) and "specs" in data:
                specs = dict(data["specs"])
                fonte = fonte or data.get("fonte", "")
            elif isinstance(data, dict):
                specs = dict(data)
            else:
                raise ValueError("arquivo deve conter dict")
        except Exception as e:
            print(json.dumps({"erro": f"arquivo ilegível: {e}"}))
            sys.exit(2)
    elif args.specs:
        try:
            specs = json.loads(args.specs)
            if not isinstance(specs, dict):
                raise ValueError("specs deve ser dict")
        except Exception as e:
            print(json.dumps({"erro": f"--specs JSON inválido: {e}"}))
            sys.exit(2)
    else:
        # Sem entrada manual: tenta o que já existe e orienta
        try:
            from src.collectors.websearch_specs import buscar_specs
            r = buscar_specs(args.modelo, args.categoria)
            if r.get("specs"):
                print(json.dumps({"aviso": "ficha já existe", "origem": r.get("origem"), "modelo": args.modelo}, ensure_ascii=False))
                return
        except Exception:
            pass
        print(json.dumps({"erro": "sem --specs nem --arquivo e sem ficha existente — forneça a ficha verificada (fonte primária)"}))
        sys.exit(2)

    salvar_ficha(args.modelo, args.categoria, specs, fonte)


if __name__ == "__main__":
    main()
