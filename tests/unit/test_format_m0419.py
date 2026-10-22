from mkt_flow_p0.format import markdown_para_html


def test_paragrafo_multilinha():
    texto = "Primeira linha\nsegunda linha"
    assert markdown_para_html(texto) == "<p>Primeira linha segunda linha</p>"


def test_paragrafos_separados():
    texto = "Primeiro paragrafo\n\nSegundo paragrafo"
    assert markdown_para_html(texto) == (
        "<p>Primeiro paragrafo</p>\n<p>Segundo paragrafo</p>"
    )


def test_titulo_separa_paragrafos():
    texto = "Introducao\n\n## Secao\nTexto"
    resultado = markdown_para_html(texto)
    assert "<h2>Secao</h2>" in resultado
    assert "<p>Texto</p>" in resultado
