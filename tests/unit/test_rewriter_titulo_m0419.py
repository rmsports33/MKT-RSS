from mkt_flow_p0.format import truncar_palavras


def test_titulo_nao_corta_palavra():
    titulo = "Samsung apresenta tecnologia inovadora para dispositivos"
    resultado = truncar_palavras(titulo, 30)
    assert resultado == "Samsung apresenta tecnologia"
    assert len(resultado) <= 30


def test_titulo_curto_preservado():
    assert truncar_palavras("Nova tecnologia", 60) == "Nova tecnologia"
