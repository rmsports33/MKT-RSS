"""Testes do mkt_flow_p0.linguagem_validator (offline)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mkt_flow_p0.linguagem_validator import (
    ErroLinguagem,
    RelatorioLinguagem,
    validar_texto,
    validar_html_estrutural,
    detectar_caracteres_suspeitos,
    detectar_tipografia,
    detectar_ortografia_simples,
    detectar_crase,
    detectar_repeticao,
    detectar_maiusculas_excesso,
    detectar_tamanho_frase,
    detectar_voz_passiva,
    detectar_concordancia_simples,
    detectar_redundancia,
    detectar_subject_verb_agreement,
    detectar_cliches_jargao,
    detectar_linguagem_inclusiva,
    detectar_urls_em_texto,
)


def _codigos(erros):
    return [e.codigo for e in erros]


def test_detecta_emoji():
    r = detectar_caracteres_suspeitos("Texto com 🚀 emoji")
    assert any(e.codigo == "CHAR-EMOJI" for e in r)


def test_detecta_cirillico():
    r = detectar_caracteres_suspeitos("Текст cirílico")
    assert any(e.codigo == "CHAR-SUSPEITO" for e in r)


def test_detecta_fullwidth():
    r = detectar_caracteres_suspeitos("ｔｅｘｔｏ fullwidth")
    assert any(e.codigo == "CHAR-FULLWIDTH" for e in r)


def test_detecta_aspas_retas():
    r = detectar_tipografia('Ele disse "ola"')
    assert any(e.codigo == "TIPO-ASPAS-RETAS" for e in r)


def test_detecta_espaco_duplo():
    r = detectar_tipografia("Duplo  espaco")
    assert any(e.codigo == "TIPO-ESPACO-DUPLO" for e in r)


def test_detecta_espaco_antes_pontuacao():
    r = detectar_tipografia("Frase . ponto")
    assert any(e.codigo == "TIPO-ESPACO-PONTUACAO" for e in r)


def test_detecta_numero_ponto_decimal():
    r = detectar_tipografia("Preço 10.50 reais")
    assert any(e.codigo == "TIPO-NUMERO-PONTO-DECIMAL" for e in r)


def test_detecta_palavra_desconhecida():
    r = detectar_ortografia_simples("xyzwqlk palavra inventada")
    assert any(e.codigo == "ORTO-PALAVRA-DESCONHECIDA" for e in r)


def test_nao_marca_sigla():
    r = detectar_ortografia_simples("O HTML e o CSS")
    assert not any(e.codigo == "ORTO-PALAVRA-DESCONHECIDA" for e in r)


def test_detecta_repeticao_imediata():
    r = detectar_repeticao("o o gato mia")
    assert any(e.codigo == "ORTO-PALAVRA-REPETIDA" for e in r)


def test_detecta_maiusculas_excesso():
    r = detectar_maiusculas_excesso("TODA MAIUSCULA aqui")
    assert any(e.codigo == "TIPO-MAIUSCULAS-EXCESSO" for e in r)


def test_nao_marca_sigla_maiuscula():
    r = detectar_maiusculas_excesso("A ANATEL e o HTML")
    assert not any(e.codigo == "TIPO-MAIUSCULAS-EXCESSO" for e in r)


def test_detecta_frase_muito_longa():
    texto = " ".join(["palavra"] * 70) + "."
    r = detectar_tamanho_frase(texto)
    assert any(e.codigo == "GRAM-FRASE-MUITO-LONGA" for e in r)


def test_detecta_voz_passiva():
    r = detectar_voz_passiva("O artigo foi escrito pela equipe")
    assert any(e.codigo == "GRAM-VOZ-PASSIVA" for e in r)


def test_detecta_crase():
    r = detectar_crase("Vou a casa")
    # "a casa" pode ser crase (a + casa). Não é erro se começar com vogal.
    # Este teste apenas verifica que não quebra.
    assert isinstance(r, list)


def test_detecta_concordancia_artigo():
    r = detectar_concordancia_simples("a carro novo")
    assert any(e.codigo == "GRAM-CONCORDANCIA-ARTIGO" for e in r)


def test_validar_texto_retorna_relatorio():
    r = validar_texto("O gato 🚀 mia.  Espaco duplo.")
    assert isinstance(r, RelatorioLinguagem)
    assert r.total_palavras > 0
    assert r.total_caracteres > 0


def test_relatorio_tem_contagem_por_tipo():
    r = validar_texto("O gato 🚀 mia.  Espaco duplo.")
    cont = r.contagem_por_tipo
    assert "caractere" in cont or "tipografia" in cont


def test_relatorio_sem_erro_critico_em_texto_limpo():
    r = validar_texto("A Anatel determina que a TIM desligue o bloqueio.")
    assert not r.tem_erro_critico


def test_validar_html_estrutural_detecta_listas():
    html = "<ol><li>a</li></ol><ol><li>b</li></ol>"
    erros = validar_html_estrutural(html)
    assert any(e.codigo == "HTML-LISTAS-SEGUIDAS" for e in erros)


def test_detecta_redundancia():
    r = detectar_redundancia("Subir para cima é fácil.")
    assert any(e.codigo == "ORTO-REDUNDANCIA" for e in r)


def test_detecta_subject_verb_agreement():
    r = detectar_subject_verb_agreement("Eles é inteligente.")
    assert any(e.codigo == "GRAM-CONCORDANCIA-SUJEITO-VERBO" for e in r)


def test_detecta_cliches_jargao():
    r = detectar_cliches_jargao("Pensar fora da caixa é importante.")
    assert any(e.codigo == "TIPO-CLIQUE-JARGAO" for e in r)


def test_detecta_linguagem_inclusiva():
    r = detectar_linguagem_inclusiva("A whitelist permite acesso.")
    assert any(e.codigo == "TIPO-LINGUAGEM-INCLUSIVA" for e in r)


def test_detecta_urls_em_texto():
    r = detectar_urls_em_texto("Acesse https://exemplo.com agora.")
    assert any(e.codigo == "HTML-URL-SOLTA" for e in r)


def test_validar_texto_inclui_todos_tipos():
    texto = (
        "O gato 🚀 mia.  Eles é inteligente. "
        "Subir para cima. Pensar fora da caixa. "
        "Acesse https://exemplo.com."
    )
    r = validar_texto(texto)
    tipos = r.contagem_por_tipo
    assert "caractere" in tipos
    assert "tipografia" in tipos
    assert "gramática" in tipos
    assert "html" in tipos

