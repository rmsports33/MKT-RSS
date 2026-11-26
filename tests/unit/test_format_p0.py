"""
Testes P0 — format (offline)
pytest tests/test_format_p0.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.format import markdown_para_html, truncar_palavras, sanitizar_url


def test_negrito_e_link():
    h = markdown_para_html("Isto é **forte** e [fonte](https://x.com/a)")
    assert "<strong>forte</strong>" in h and '<a href="https://x.com/a"' in h
    assert "**" not in h


def test_headings_listas_hr():
    md = "## Título\n\n1. Um\n2. Dois\n\n- A\n- B\n\n---\n\nTexto"
    h = markdown_para_html(md)
    assert "<h2>Título</h2>" in h and "<ol>" in h and "<ul>" in h and "<hr>" in h


def test_xss_escapado_antes_do_bold():
    h = markdown_para_html('<script>alert(1)</script> **ok**')
    assert "<script>" not in h and "<strong>ok</strong>" in h


def test_truncar_fronteira():
    assert truncar_palavras("Fabricantes opinam sobre isso", 20) == "Fabricantes opinam"
    assert truncar_palavras("Curto", 60) == "Curto"
    assert "opi" not in truncar_palavras("Fabricantes opinam", 16).split()[-1:]


def test_sanitizar_url():
    assert sanitizar_url("https://x.com/vaza-odispositivo/") == "https://x.com/vaza-odispositivo/"
    assert "­" not in sanitizar_url("https://x.com/vaza-o­dispositivo/")
    assert sanitizar_url("https://x.com/a" + chr(0) + "b ") == "https://x.com/ab"


def test_table_from_live_draft_uses_same_renderer_as_offline_core():
    from mkt_flow_p0.editorial_core_offline import _renderizar_markdown_editorial
    markdown = '## Custos\n\n| Opção | Valor |\n|---|---|\n| Compra | 20.000 |\n| Assinatura | <script>x</script> |'
    html = markdown_para_html(markdown)
    assert '<table>' in html and '<th>Opção</th>' in html
    assert '<script>' not in html and '&lt;script&gt;' in html
    assert '<p>|' not in html
    assert html == _renderizar_markdown_editorial(markdown)


def test_linhas_quebradas_formam_um_paragrafo():
    """Quebra de linha de 78 colunas é visual: não vira um <p> por linha."""
    md = ("A Anatel determinou, em caráter cautelar,\n"
          "que a TIM desligue a ferramenta.\n"
          "\n"
          "Outro parágrafo aqui.")
    h = markdown_para_html(md)
    assert h.count("<p>") == 2
    assert "<p>A Anatel determinou, em caráter cautelar, que a TIM desligue a ferramenta.</p>" in h
    assert "<p>Outro parágrafo aqui.</p>" in h
    assert "cautelar,\n" not in h


def test_item_de_lista_numerada_nao_reinicia_por_quebra_de_linha():
    md = ("1. **Primeiro** item com\n"
          "   continuação na linha de baixo.\n"
          "2. Segundo.\n"
          "3. Terceiro com\n"
          "   continuação.\n"
          "\n"
          "Texto depois da lista.")
    h = markdown_para_html(md)
    assert h.count("<ol>") == 1 and h.count("</ol>") == 1
    assert h.count("<li>") == 3
    assert "<li><strong>Primeiro</strong> item com continuação na linha de baixo.</li>" in h
    assert "<li>Terceiro com continuação.</li>" in h
    assert "<p>Texto depois da lista.</p>" in h
    after_list = h.split("</ol>", 1)[1]
    assert "<li>" not in after_list


def test_lista_com_marcador_aceita_continuacao():
    md = ("- **Primeiro**: frase longa que\n"
          "  continua aqui.\n"
          "- **Segundo**: outra.\n"
          "\n"
          "Fim.")
    h = markdown_para_html(md)
    assert h.count("<ul>") == 1 and h.count("<li>") == 2
    assert "<li><strong>Primeiro</strong>: frase longa que continua aqui.</li>" in h


def test_formatacao_inline_dentro_de_celula_de_tabela():
    md = ("| Item | Situação |\n"
          "|---|---|\n"
          "| Despacho | **pendente** e <b>cru</b> |")
    h = markdown_para_html(md)
    assert "<td><strong>pendente</strong> e &lt;b&gt;cru&lt;/b&gt;</td>" in h
    assert "**" not in h


def test_rascunho_9900_nao_quebra_frase_em_varios_paragrafos():
    """Regressão do #9900 (17/11/2026): 58 <p> e 4 listas numeradas viraram 16 e 2."""
    from pathlib import Path
    md_path = Path(__file__).parent.parent.parent / "artigos-pendentes" / "2026-11-17" / "anatel-tim-antispam.md"
    if not md_path.exists():
        return  # insumo editorial não versionado
    h = markdown_para_html(md_path.read_text(encoding="utf-8"))
    assert h.count("<ol>") == 2, "listas numeradas não devem reiniciar a cada item"
    assert h.count("<ul>") == 2
    assert h.count("<p>") <= 20
    # nenhum parágrafo do corpo pode terminar sem pontuação final (frase partida)
    import re as _re
    corpo_html = h.split("<h2>Fontes</h2>", 1)[0]
    corpo_html = corpo_html.split("<p>A Agência Nacional", 1)[1]
    finais = (".", "!", "?", ":", ";", '"', ")", "…")
    for corpo in _re.findall(r"<p>(.*?)</p>", corpo_html):
        texto = _re.sub(r"<[^>]+>", "", corpo).strip()
        assert texto.endswith(finais), f"parágrafo partido: ...{texto[-60:]!r}"
