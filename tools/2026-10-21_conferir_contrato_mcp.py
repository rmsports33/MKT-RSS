# -*- coding: utf-8 -*-
"""Confere o contrato do adaptador contra o servidor MCP REAL (21/10/2026).

Por que existe: o adaptador `gerar_comparativo → create_comparativo` foi
escrito lendo o PHP do tema. Ler o código da copia local e achar que o
servidor aceita os mesmos nomes e' a forma classica de construir um
adaptador que so funciona contra o codigo, nao contra o servidor.

Este script consulta o catalogo de ferramentas do MCP (GET publico, leitura
mesmo) e compara com o que o adaptador produz:
  - toda chave gerada precisa estar declarada no servidor;
  - toda chave declarada que o adaptador usa precisa ser gerada;
  - os limites (maximo de produtos e de criterios) sao conferidos.

Nao grava, nao publica, nao chama a ferramenta — so LE o catalogo.

Uso:
    python tools/2026-10-21_conferir_contrato_mcp.py

Exit 0 = contrato conferido. Exit 1 = divergencia. Exit 2 = nao deu para ler.
"""
import json
import sys
from pathlib import Path
from urllib.request import Request, build_opener

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from mkt_flow_p0.comparativo_contract import (  # noqa: E402
    MAX_CRITERIOS_MCP,
    MAX_PRODUTOS_MCP,
    construir_contrato,
    contrato_para_mcp,
)

URL_TOOLS = "https://conexotech.com.br/wp-json/conexo/v1/mcp/tools"
NOME_TOOL = "create_comparativo"


def ler_catalogo():
    req = Request(URL_TOOLS, headers={"Accept": "application/json",
                                      "User-Agent": "ConexoTech-M04.17B/1.0"})
    with build_opener().open(req, timeout=30) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def main():
    print("CONFERENCIA DO CONTRATO DO ADAPTADOR CONTRA O MCP REAL")
    print(f"catalogo: {URL_TOOLS}\n")
    try:
        catalogo = ler_catalogo()
    except Exception as erro:  # noqa: BLE001
        print("ERRO: nao foi possivel ler o catalogo: %s" % erro)
        return 2

    ferramentas = catalogo.get("tools") if isinstance(catalogo, dict) else catalogo
    if isinstance(ferramentas, dict):
        ferramentas = ferramentas.get("tools") or []
    alvo = None
    for ferramenta in ferramentas or []:
        if not isinstance(ferramenta, dict):
            continue
        # O servidor publica o NOME da ferramenta na chave "tool" (o catalogo
        # tem {tool, description, params, write}). Aceitamos "name" tambem
        # para o script nao depender de um unico formato.
        nome = ferramenta.get("tool") or ferramenta.get("name")
        if nome == NOME_TOOL:
            alvo = ferramenta
            break
    if alvo is None:
        disponiveis = [t.get("tool") or t.get("name") for t in (ferramentas or [])
                       if isinstance(t, dict)]
        print(f"ERRO: ferramenta {NOME_TOOL} nao encontrada no catalogo")
        print(f"      disponiveis: {disponiveis}")
        return 2

    declarados = list(alvo.get("params") or [])
    print(f"ferramenta: {NOME_TOOL}")
    print(f"params declarados no servidor: {declarados}")

    # Gera um contrato minimo valido e converte.
    contrato = construir_contrato(
        modelos=[
            {"nome": "Produto A", "specs": {}, "fonte": "https://news.samsung.com/br/a"},
            {"nome": "Produto B", "specs": {}, "fonte": "https://store.google.com/pt/b"},
        ],
        price_history={
            "Produto A": [{"data": "2026-09-17", "preco": 100.0,
                           "fonte": "https://www.amazon.com.br/dp/A"}],
            "Produto B": [{"data": "2026-09-17", "preco": 200.0,
                           "fonte": "https://www.mercadolivre.com.br/b"}],
        },
        conteudo_html="<p>conteudo</p>",
        titulo="A vs B",
        notas={"Produto A": 8.0, "Produto B": 7.5},
        compras={"Produto A": "https://www.amazon.com.br/dp/A",
                 "Produto B": "https://www.mercadolivre.com.br/b"},
        criterios=[{"label": "Preco", "vals": ["R$ 100,00", "R$ 200,00"], "win": 0}],
    )
    params = contrato_para_mcp(contrato)
    gerados = sorted(params.keys())

    print(f"params gerados pelo adaptador: {gerados}\n")

    erros = []
    fora = [k for k in gerados if k not in declarados]
    if fora:
        erros.append(f"o adaptador gera parametro(s) que o servidor NAO declara: {fora}")
    faltando = [k for k in declarados if k not in gerados]
    if faltando:
        erros.append(f"o servidor declara parametro(s) que o adaptador nao gera: {faltando}")

    print(f"limites: produtos <= {MAX_PRODUTOS_MCP}, criterios <= {MAX_CRITERIOS_MCP}")
    if len(params.get("products") or []) > MAX_PRODUTOS_MCP:
        erros.append("mais produtos que o MCP aceita")
    if len(params.get("crits") or []) > MAX_CRITERIOS_MCP:
        erros.append("mais criterios que o MCP aceita")

    print()
    if erros:
        print("RESULTADO: DIVERGENCIA — %d problema(s):" % len(erros))
        for erro in erros:
            print(f"  - {erro}")
        return 1
    print("RESULTADO: CONFERIDO — o adaptador gera exatamente os parametros que o "
          "servidor MCP declara, e nos limites que ele aceita")
    return 0


if __name__ == "__main__":
    sys.exit(main())
