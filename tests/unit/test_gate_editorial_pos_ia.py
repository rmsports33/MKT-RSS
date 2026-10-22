from mkt_flow_p0.gate_editorial_pos_ia import validar_saida


def test_bloqueia_teste_inventado():
    resultado = validar_saida("A empresa anunciou um produto.", "Avaliamos o produto.")
    assert resultado["veredito"] == "BLOQUEADO"


def test_bloqueia_preco_novo():
    resultado = validar_saida("Novo produto anunciado.", "O preco e R$ 1.709.")
    assert resultado["veredito"] == "BLOQUEADO"


def test_bloqueia_numero_novo():
    resultado = validar_saida("Produto anunciado.", "O aparelho tem 512 GB.")
    assert resultado["veredito"] == "BLOQUEADO"


def test_texto_sem_alertas():
    resultado = validar_saida(
        "O produto possui 256 GB.",
        "O produto possui 256 GB."
    )
    assert resultado["veredito"] == "SEM_ALERTAS"
