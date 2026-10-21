# -*- coding: utf-8 -*-
"""Prova de compatibilidade do contrato legado M04.16C (21/10/2026, M04.17A).

Por que existe: o M04.17A adicionou `produtos`/`exigir_produtos` ao gate.
"Aditivo" no papel nao e' prova. Este script carrega a implementacao ANTIGA
(M04.16C) e a NOVA, chama as duas com os mesmos argumentos legados e compara:

  1. o VEREDITO e os CRITERIOS de cada caso legado — tem que ser identico;
  2. as CHAVES do resultado — a nova tem que ter TODAS as chaves da antiga
     (superset), nunca menos.

Divergência em qualquer um dos dois = quebra de contrato.

Uso:
    python tools/2026-10-21_compatibilidade_m0416c.py \
        --antigo "C:\\caminho\\para\\master\\mkt_flow_p0\\content_filter.py"

Exit 0 = compativel. Exit 1 = QUEBRADO. Exit 2 = nao foi possivel comparar.
"""
import argparse
import importlib.util
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
AUDITOR = Path(__file__).resolve().with_name("2026-10-21_auditar_gate_valor.py")


def _carregar_auditor():
    spec = importlib.util.spec_from_file_location("auditor_gate", AUDITOR)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--antigo", required=True, help="content_filter.py do M04.16C")
    ap.add_argument("--novo", default=str(RAIZ / "mkt_flow_p0" / "content_filter.py"))
    args = ap.parse_args()

    auditor = _carregar_auditor()
    print("COMPATIBILIDADE DO CONTRATO LEGADO (M04.16C -> M04.17A)")
    print(f"antigo: {args.antigo}")
    print(f"novo:   {args.novo}\n")

    try:
        antigo, _ = auditor.carregar(Path(args.antigo))
        novo, _ = auditor.carregar(Path(args.novo))
    except Exception as erro:  # noqa: BLE001
        print("ERRO: nao foi possivel carregar as implementacoes: %s" % erro)
        return 2

    # Casos legados: os do auditor que NAO usam o contrato novo.
    legados = list(auditor.CASOS_ADVERSARIAIS) + list(auditor.CASOS_POSITIVOS)

    divergencias = []
    for nome, kwargs, _ in legados:
        try:
            r_antigo = antigo.filtrar_valor_acrescentado(**kwargs)
        except Exception as erro:  # noqa: BLE001
            print(f"  ERRO   {nome}: implementacao antiga levantou {erro}")
            divergencias.append(nome)
            continue
        try:
            r_novo = novo.filtrar_valor_acrescentado(**kwargs)
        except Exception as erro:  # noqa: BLE001
            print(f"  ERRO   {nome}: implementacao nova levantou {erro}")
            divergencias.append(nome)
            continue

        iguais = (r_antigo.get("veredito") == r_novo.get("veredito")
                  and (r_antigo.get("criterios") or []) == (r_novo.get("criterios") or [])
                  and r_antigo.get("motivo") == r_novo.get("motivo"))
        if iguais:
            print(f"  OK    {nome}: {r_novo.get('veredito')} {r_novo.get('criterios') or ''}")
        else:
            divergencias.append(nome)
            print(f"  FALHA {nome}:")
            print(f"        antigo: {r_antigo.get('veredito')} "
                  f"{r_antigo.get('criterios') or ''} motivo={r_antigo.get('motivo')}")
            print(f"        novo:   {r_novo.get('veredito')} "
                  f"{r_novo.get('criterios') or ''} motivo={r_novo.get('motivo')}")

    # O conjunto de chaves do resultado antigo tem que estar contido no novo.
    print("\nCHAVES DO RESULTADO")
    amostra = dict(legados[0][1])
    chaves_antigas = set(antigo.filtrar_valor_acrescentado(**amostra).keys())
    chaves_novas = set(novo.filtrar_valor_acrescentado(**amostra).keys())
    faltando = chaves_antigas - chaves_novas
    if faltando:
        divergencias.append("chaves_perdidas")
        print(f"  FALHA chaves perdidas na versao nova: {sorted(faltando)}")
    else:
        print(f"  OK    todas as {len(chaves_antigas)} chaves legadas existem na nova")
    print(f"        chaves novas (aditivas): {sorted(chaves_novas - chaves_antigas)}")

    print()
    if divergencias:
        print(f"RESULTADO: QUEBRADO — {len(divergencias)} divergencia(s):")
        for d in divergencias:
            print(f"  - {d}")
        return 1
    print(f"RESULTADO: COMPATIVEL — {len(legados)} casos legados com veredito e "
          "criterios identicos, e nenhuma chave perdida")
    return 0


if __name__ == "__main__":
    sys.exit(main())
