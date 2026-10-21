# -*- coding: utf-8 -*-
"""21/10/2026 — Prova a fronteira redator -> WordPress (Issue #5 / Issue #6).

Pergunta que este script responde, com evidencia e sem rede:
    o que `gerar_comparativo` produz cabe no campo `content` que o
    `wp_publisher` manda para /wp-json/wp/v2/posts?

Por que importa: o WordPress guarda `content` como conteudo de post e o tema
renderiza dentro de `.entry-content`. Documento completo (<!DOCTYPE>, <head>,
<script>, <style>) nao e' fragmento de post. Publicar assim produz HTML
aninhado invalido — e o site ja mostra sinal disso (</p> solto dentro de
<nav class="toc"> na pagina real, ver relatorio da sessao).

O que o script NAO faz: nao chama LLM (fake injetado), nao chama rede, nao
escreve no WordPress. So monta o HTML e mede a forma dele.

Uso:
    python tools/2026-10-21_provar_integracao_redator_wp.py \
        --redator "C:/.../nexobot-s3-redator"

Saida: tabela de checagens + lista de campos exigidos pelo MCP que a saida do
redator nao entrega. Codigo 0 = relatorio gerado (nao e' gate de publicacao).
"""
import argparse
import json
import sys
from pathlib import Path

# Contrato que o MCP do tema espera em create_comparativo (lido de
# conexotech/inc-mcp-server.php e de /wp-json/conexo/v1/mcp/tools).
MCP_CAMPOS_COMPARATIVO = ["title", "content", "products", "notas", "crits",
                          "veredito", "buys", "cat_slug"]
# Payload que o wp_publisher realmente envia (mkt_flow_p0/wp_publisher.py).
WP_PUBLISHER_CAMPOS = ["title", "content", "status", "categories", "tags",
                       "featured_media", "slug"]


def _modelos():
    return [
        {"nome": "Fone A", "specs": {"bateria.mah": "5000", "peso.g": "200"},
         "fonte": "fabricante A", "data_lancamento": "2026-08"},
        {"nome": "Fone B", "specs": {"bateria.mah": "4000", "peso.g": "180"},
         "fonte": "fabricante B", "data_lancamento": "2026-07"},
    ]


def _llm_fake(system, payload):
    return ("<h2>Vale a pena?</h2><p>Depende do uso. O Fone A tem mais bateria.</p>"
            "<h2>Bateria</h2><p>5000 mAh contra 4000 mAh.</p>")


def medir(html):
    return {
        "bytes": len(html.encode("utf-8")),
        "doctype": html.lstrip().lower().startswith("<!doctype"),
        "tag_html": "<html" in html.lower(),
        "tag_head": "<head" in html.lower(),
        "tag_body": "<body" in html.lower(),
        "tag_script": "<script" in html.lower(),
        "tag_style": "<style" in html.lower(),
        "tag_meta": "<meta" in html.lower(),
        "tag_link": "<link" in html.lower(),
        "campos_conexo": html.count("_conexo_"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--redator", required=True,
                    help="raiz do clone do bot-redator-artigo (tem src/generator/render.py)")
    ap.add_argument("--saida", default="",
                    help="grava o relatorio em UTF-8 neste arquivo")
    args = ap.parse_args()

    raiz = Path(args.redator).resolve()
    if not (raiz / "src" / "generator" / "render.py").is_file():
        raise SystemExit("nao achei src/generator/render.py em %s" % raiz)
    sys.path.insert(0, str(raiz))

    from src.generator.render import gerar_comparativo  # noqa: E402

    saida = gerar_comparativo(_modelos(), "audio", chamar_llm=_llm_fake)
    html = saida.get("html", "")
    if not html:
        raise SystemExit("gerar_comparativo nao devolveu html: %s" % list(saida))

    m = medir(html)
    linhas = [
        ("chave de saida", ", ".join(sorted(saida.keys()))),
        ("tamanho do html", "%d bytes" % m["bytes"]),
        ("comeca com <!DOCTYPE>", "SIM" if m["doctype"] else "nao"),
        ("contem <html>", "SIM" if m["tag_html"] else "nao"),
        ("contem <head>", "SIM" if m["tag_head"] else "nao"),
        ("contem <body>", "SIM" if m["tag_body"] else "nao"),
        ("contem <script>", "SIM" if m["tag_script"] else "nao"),
        ("contem <style>", "SIM" if m["tag_style"] else "nao"),
        ("contem <meta>", "SIM" if m["tag_meta"] else "nao"),
        ("contem <link>", "SIM" if m["tag_link"] else "nao"),
        ("campos _conexo_ no html", str(m["campos_conexo"])),
    ]

    rel = ["Fronteira redator -> WordPress", "=" * 78]
    for rotulo, valor in linhas:
        rel.append("  %-28s %s" % (rotulo, valor))

    documento = m["doctype"] and m["tag_html"] and m["tag_head"] and m["tag_body"]
    rel.append("\nVeredito de forma:")
    if documento:
        rel.append("  DOCUMENTO COMPLETO — nao e' fragmento de post.")
        rel.append("  wp_publisher manda isto em `content`; o tema renderiza dentro de")
        rel.append("  `.entry-content`, gerando html/head/body aninhados.")
    else:
        rel.append("  fragmento de post (ok para content)")

    # O redator devolve `html` + `auditoria`; o MCP precisa de campos separados.
    faltando = [c for c in MCP_CAMPOS_COMPARATIVO if c not in ("title", "content")]
    rel.append("\nContrato do MCP create_comparativo vs saida do redator:")
    rel.append("  title   -> vem como `titulo` na saida (nome diferente do campo MCP)")
    rel.append("  content -> entregue como `html` (documento completo)")
    for campo in faltando:
        rel.append("  %-7s -> AUSENTE na saida do redator" % campo)

    rel.append("\nPayload do wp_publisher (enviado hoje):")
    rel.append("  " + ", ".join(WP_PUBLISHER_CAMPOS))
    rel.append("  -> nao envia meta _conexo_*; cria post_type `post` (nao review/comparativo)")

    rel.append("\nSobrevivencia ao wp_kses_post (analise estatica):")
    rel.append("  WP remove <script>, <style>, <link>, <meta>, <html>, <head>, <body>")
    rel.append("  para quem NAO tem unfiltered_html; para admin, o <script> passa.")
    rel.append("  Logo o mesmo HTML se comporta diferente conforme o usuario do token.")

    saida_json = Path(__file__).with_name("_saida_integracao_redator_wp.json")
    saida_json.write_text(json.dumps({"medidas": m, "documento": documento,
                                      "mcp_faltando": faltando,
                                      "redator": str(raiz)},
                                     ensure_ascii=False, indent=2), encoding="utf-8")
    rel.append("\nJSON: %s" % saida_json.name)

    texto = "\n".join(rel)
    print(texto)
    if args.saida:
        Path(args.saida).write_text(texto + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
