# -*- coding: utf-8 -*-
"""21/10/2026 — Auditoria adversarial do gate de valor (Issue #9 / M04.16).

Por que existe: a Issue #9 afirma que o gate local do MKT-RSS e' fail-open em
tres pontos — aprova preco sem data, aprova data sem preco, aprova cruzamento
sinalizado com uma unica fonte. Este script NAO confia na afirmacao nem no
conserto: carrega o modulo por caminho e roda a mesma matriz de casos contra
implementacoes diferentes, mostrando veredito observado x esperado.

Regra 4 do AGENTS.md aplicada ao proprio gate: todo caso tem que reprovar
quando deve reprovar. Um gate que aprova tudo passa em todos os testes.

Uso:
    python tools/2026-10-21_auditar_gate_valor.py --modulo <caminho/content_filter.py>
    python tools/2026-10-21_auditar_gate_valor.py --modulo A --modulo B

Saida: tabela por caso. Codigos: 0 = todos os casos fail-open conforme o
esperado; 1 = algum caso divergiu (gate fail-open ou fail-closed demais);
2 = modulo sem `filtrar_valor_acrescentado` (gate ausente = tudo passa).

Nenhuma escrita de arquivo, nenhuma rede, nenhum import de terceiro.
"""
import argparse
import importlib.util
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

CASOS = [
    # --- secao 1: as tres falhas nomeadas na Issue #9 ---------------------
    {
        "id": "preco-sem-data",
        "grupo": "fail_open",
        "kwargs": {
            "titulo": "iPhone 17e",
            "texto": "O iPhone 17e saiu por R$ 4.049 na Amazon.",
            "links": ["https://www.amazon.com.br/dp/B0X"],
        },
        "esperado": "BLOQUEADO",
        "nota": "preco sem data de captura nao e' evidencia (regra 13)",
    },
    {
        "id": "data-sem-preco",
        "grupo": "fail_open",
        "kwargs": {
            "titulo": "Galaxy A37",
            "texto": "Captura feita em 27/09/2026 no marketplace.",
            "links": ["https://www.amazon.com.br/dp/B0Y"],
        },
        "esperado": "BLOQUEADO",
        "nota": "data solta nao e' preco",
    },
    {
        "id": "cruzamento-1-fonte",
        "grupo": "fail_open",
        "kwargs": {
            "titulo": "Novidade",
            "texto": "Cruzamos os dados.",
            "links": ["https://www.canaltech.com.br/materia/x"],
            "tem_cruzamento": True,
        },
        "esperado": "BLOQUEADO",
        "nota": "flag declarada sem 2 dominios independentes",
    },
    # --- secao 2: variantes da mesma classe ------------------------------
    {
        "id": "preco-data-fonte-nao-comercial",
        "grupo": "fail_open",
        "kwargs": {
            "titulo": "Fone X",
            "texto": "Sai por R$ 1.299 em 20/10/2026.",
            "links": ["https://www.canaltech.com.br/materia/y"],
        },
        "esperado": "BLOQUEADO",
        "nota": "preco tem que vir de marketplace onde o dono e' afiliado",
    },
    {
        "id": "data-calendario-invalida",
        "grupo": "fail_open",
        "kwargs": {
            "titulo": "TV Z",
            "texto": "Sai por R$ 2.131 em 31/02/2026.",
            "links": ["https://www.kabum.com.br/produto/1"],
        },
        "esperado": "BLOQUEADO",
        "nota": "31/02 nao existe: data inventada",
    },
    {
        "id": "marketplace-como-fonte-primaria",
        "grupo": "fail_open",
        "kwargs": {
            "titulo": "Capa de celular",
            "texto": "A empresa anunciou uma nova linha de produtos.",
            "links": ["https://www.mercadolivre.com.br/p/MLB123"],
        },
        "esperado": "BLOQUEADO",
        "nota": "marketplace nao e' fonte primaria oficial",
    },
    # --- secao 3: controles positivos (o gate tem que APROVAR) -----------
    {
        "id": "preco-data-marketplace",
        "grupo": "controle_positivo",
        "kwargs": {
            "titulo": "Fone X",
            "texto": "Sai por R$ 1.299 em 20/10/2026.",
            "links": ["https://www.kabum.com.br/produto/1"],
        },
        "esperado": "APROVADO",
        "nota": "criterio 1 completo",
    },
    {
        "id": "fonte-primaria-oficial",
        "grupo": "controle_positivo",
        "kwargs": {
            "titulo": "Galaxy S26",
            "texto": "A Samsung divulgou a ficha do aparelho.",
            "links": ["https://news.samsung.com/br/galaxy-s26-anuncio"],
        },
        "esperado": "APROVADO",
        "nota": "criterio 2 completo",
    },
    {
        "id": "medicao-propria",
        "grupo": "controle_positivo",
        "kwargs": {
            "titulo": "Galaxy S26",
            "texto": "Testamos o Galaxy S26 por 30 dias.",
            "links": [],
        },
        "esperado": "APROVADO",
        "nota": "criterio 3 completo",
    },
    {
        "id": "video-transcrito",
        "grupo": "controle_positivo",
        "kwargs": {
            "titulo": "Review em video",
            "texto": "Transcricao do review do YouTube.",
            "links": [],
            "tem_video": True,
        },
        "esperado": "APROVADO",
        "nota": "criterio 3 (video) completo",
    },
    {
        "id": "cruzamento-2-fontes",
        "grupo": "controle_positivo",
        "kwargs": {
            "titulo": "Comparativo",
            "texto": "Tabela com criterio explicito.",
            "links": ["https://www.canaltech.com.br/a",
                      "https://www.tecmundo.com.br/b"],
            "tem_cruzamento": True,
        },
        "esperado": "APROVADO",
        "nota": "criterio 4 completo",
    },
    # --- secao 4: controle negativo (nada de valor) ----------------------
    {
        "id": "texto-neutro",
        "grupo": "controle_positivo",
        "kwargs": {
            "titulo": "Noticia",
            "texto": "A empresa anunciou uma nova linha de produtos.",
            "links": [],
        },
        "esperado": "BLOQUEADO",
        "nota": "sem nenhum dos 4 criterios = digest, nao artigo",
    },
    # --- secao 5: lacuna estrutural declarada na Issue #9 ----------------
    {
        "id": "comparativo-preco-de-1-de-2-produtos",
        "grupo": "lacuna",
        "kwargs": {
            "titulo": "Fone A vs Fone B",
            "texto": "O Fone A sai por R$ 1.299 em 20/10/2026.",
            "links": ["https://www.kabum.com.br/produto/1"],
        },
        "esperado": "BLOQUEADO",
        "nota": "Issue #9 pede evidencia POR PRODUTO; a assinatura atual "
                "nao recebe produto, entao o gate aprova o comparativo inteiro",
    },
]


def carregar(caminho):
    caminho = Path(caminho).resolve()
    if not caminho.is_file():
        raise SystemExit("arquivo nao existe: %s" % caminho)
    spec = importlib.util.spec_from_file_location("alvo_%s" % abs(hash(str(caminho))), caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def avaliar(nome, modulo):
    gate = getattr(modulo, "filtrar_valor_acrescentado", None)
    if not callable(gate):
        print("\n%s" % nome)
        print("  GATE AUSENTE: modulo nao expoe filtrar_valor_acrescentado")
        print("  Verdade pratica: sem gate, todo item segue para artigo.")
        return "AUSENTE", []

    print("\n%s" % nome)
    print("  %-38s %-12s %-12s %s" % ("caso", "esperado", "observado", "situacao"))
    print("  " + "-" * 82)
    falhas = []
    for caso in CASOS:
        resultado = gate(**caso["kwargs"])
        observado = resultado.get("veredito", "?")
        ok = observado == caso["esperado"]
        if not ok and caso["grupo"] != "lacuna":
            falhas.append(caso["id"])
        marca = "ok" if ok else ("LACUNA" if caso["grupo"] == "lacuna" else "DIVERGE")
        print("  %-38s %-12s %-12s %s" % (caso["id"], caso["esperado"], observado, marca))
        if not ok:
            print("     -> %s" % caso["nota"])
    return "OK" if not falhas else "FAIL", falhas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modulo", action="append", required=True,
                    help="caminho do content_filter.py a auditar (repetivel)")
    ap.add_argument("--saida", default="",
                    help="grava o relatorio em UTF-8 neste arquivo (console mente sobre acento)")
    args = ap.parse_args()

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        resumo = []
        for caminho in args.modulo:
            modulo = carregar(caminho)
            estado, falhas = avaliar(caminho, modulo)
            resumo.append((caminho, estado, falhas))

        print("\n" + "=" * 86)
        print("RESUMO")
        for caminho, estado, falhas in resumo:
            print("  %-10s %s" % (estado, caminho))
            if falhas:
                print("             divergencias: %s" % ", ".join(falhas))

    texto = buffer.getvalue()
    sys.stdout.write(texto)
    if args.saida:
        Path(args.saida).write_text(texto, encoding="utf-8")

    if any(estado == "AUSENTE" for _, estado, _ in resumo):
        return 2
    if any(estado == "FAIL" for _, estado, _ in resumo):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
