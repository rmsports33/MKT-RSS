"""Testes do reparo de parágrafos em HTML já renderizado (offline)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mkt_flow_p0.html_paragrafos import listas_seguidas, reparar_paragrafos


def _palavras(html_):
    texto = re.sub(r"<[^>]+>", " ", html_)
    return re.findall(r"[0-9A-Za-zÀ-ÿ]+", texto.lower())


def test_junta_paragrafos_que_continuam_a_frase():
    quebrado = "<p>A TIM não cumpriu</p>\n<p>as obrigações.</p>"
    assert reparar_paragrafos(quebrado) == "<p>A TIM não cumpriu as obrigações.</p>"


def test_nao_junta_paragrafos_de_frases_inteiras():
    certo = "<p>Primeira frase.</p>\n<p>Segunda frase.</p>"
    assert reparar_paragrafos(certo) == certo


def test_ponto_e_virgula_no_fim_tambem_continua():
    quebrado = "<p>O recado é simples: permitido;</p>\n<p>proibido sem explicar.</p>"
    assert reparar_paragrafos(quebrado) == "<p>O recado é simples: permitido; proibido sem explicar.</p>"


def test_devolve_continuacao_para_dentro_do_item():
    quebrado = "<ol>\n<li>Garantir atendimento</li>\n</ol>\n<p>feitas pela agência.</p>"
    assert reparar_paragrafos(quebrado) == "<ol>\n<li>Garantir atendimento feitas pela agência.</li></ol>"


def test_une_listas_separadas_pelo_mesmo_texto_fragmentado():
    quebrado = ("<ol>\n<li>Um</li>\n</ol>\n<p>meio do item</p>\n<ol>\n<li>Dois</li>\n</ol>")
    reparado = reparar_paragrafos(quebrado)
    assert reparado.count("<ol>") == 1 and reparado.count("</ol>") == 1
    assert reparado.count("<li>") == 2
    assert "meio do item" in reparado


def test_nao_engole_imagem_nem_tabela():
    quebrado = ('<p>Texto antes</p>\n<p><img src="a.jpg" alt="x"></p>\n'
                '<div class="rolagem"><table><tbody><tr><td>célula</td></tr></tbody></table></div>')
    reparado = reparar_paragrafos(quebrado)
    assert "<img" in reparado and "<table>" in reparado
    assert '<p>Texto antes</p>' in reparado


def test_idempotente():
    quebrado = "<p>Frase cortada aqui,</p>\n<p>e termina.</p>"
    uma = reparar_paragrafos(quebrado)
    assert reparar_paragrafos(uma) == uma


def test_listas_seguidas_conta_fragmentacao():
    assert listas_seguidas("<ol><li>a</li></ol><ol><li>b</li></ol>") == 1
    assert listas_seguidas("<ol><li>a</li></ol><p>x</p><ul><li>b</li></ul>") == 0


def test_rascunho_9900_reparado_sem_perder_palavra():
    origem = (Path(__file__).parent.parent.parent / "artigos-pendentes" / "2026-11-17"
              / "anatel-tim-antispam.md")
    if not origem.exists():
        return  # insumo editorial não versionado
    # reproduz o defeito original: um <p> por linha do arquivo
    quebrado = "\n".join(f"<p>{linha}</p>"
                         for linha in origem.read_text(encoding="utf-8").splitlines()
                         if linha.strip())
    reparado = reparar_paragrafos(quebrado)
    assert _palavras(reparado) == _palavras(quebrado)
    assert reparado.count("<p>") < quebrado.count("<p>") / 2
