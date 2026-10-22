import pytest

from mkt_flow_p0.gate_editorial_pos_ia import validar_saida


@pytest.mark.parametrize("nome,fonte,artigo,esperado", [
    ("preco_igual", "Custa R$ 1.709,00.", "O preco e R$ 1.709,00.", "SEM_ALERTAS"),
    ("preco_alterado", "Custa R$ 1.709,00.", "O preco e R$ 1.799,00.", "BLOQUEADO"),
    ("ano_sem_evidencia", "Novo celular anunciado.", "O celular chega em 2027.", "BLOQUEADO"),
    ("teste_inventado", "Fabricante anunciou um notebook.", "Testamos o notebook.", "BLOQUEADO"),
    ("especificacao_nova", "Produto anunciado.", "Possui 512 GB.", "BLOQUEADO"),
    ("numero_novo_formato", "Possui 1 TB.", "Possui 1024 GB.", "BLOQUEADO"),
    ("informacao_correta", "Possui 256 GB.", "O dispositivo possui 256 GB.", "SEM_ALERTAS"),
])
def test_precisao_editorial(nome, fonte, artigo, esperado):
    resultado = validar_saida(fonte, artigo)
    assert resultado["veredito"] == esperado, nome
