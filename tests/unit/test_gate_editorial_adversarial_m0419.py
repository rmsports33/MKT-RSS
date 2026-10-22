"""Regressões adversariais da M04.19P: seis falhas reproduzidas."""
import pytest
from mkt_flow_p0.gate_editorial_pos_ia import validar_saida

@pytest.mark.parametrize("nome,fonte,artigo,esperado", [
    ("numero_contexto", "Modelo A: 256 GB. Modelo B: 512 GB.",
     "Modelo A: 512 GB.", "BLOQUEADO"),
    ("preco_contexto", "Produto A custa R$ 1.000. Produto B custa R$ 2.000.",
     "Produto A custa R$ 2.000.", "BLOQUEADO"),
    ("teste_equipe", "Fabricante apresentou um novo fone.",
     "Nossa equipe testou o novo fone.", "BLOQUEADO"),
    ("data_equivalente", "Lancamento em 22 de outubro de 2026.",
     "Lancamento em 22/10/2026.", "SEM_ALERTAS"),
    ("citacao_empresa", "A empresa afirmou: testamos 10 prototipos.",
     "Segundo a empresa, testamos 10 prototipos.", "SEM_ALERTAS"),
    ("preco_reais", "O preco e R$ 1.709,00.",
     "O aparelho custa 1.709,00 reais.", "SEM_ALERTAS"),
])
def test_seis_falhas_conhecidas(nome, fonte, artigo, esperado):
    assert validar_saida(fonte, artigo)["veredito"] == esperado, nome
