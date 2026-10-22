from unittest.mock import patch

import pytest

import pipeline_rss as P
from mkt_flow_p0.gate_editorial_pos_ia import validar_saida


def test_gate_bloqueia_alegacao_de_teste():
    resultado = validar_saida(
        "A empresa anunciou um produto.",
        "Avaliamos o produto em nossos testes."
    )
    assert resultado["veredito"] == "BLOQUEADO"


def test_gate_bloqueia_numero_sem_fonte():
    resultado = validar_saida(
        "A fabricante anunciou o dispositivo.",
        "O dispositivo custa R$ 1.709."
    )
    assert resultado["veredito"] == "BLOQUEADO"


def test_gate_aceita_numero_presente_na_fonte():
    resultado = validar_saida(
        "O dispositivo tem 256 GB.",
        "O dispositivo tem 256 GB."
    )
    assert resultado["veredito"] == "SEM_ALERTAS"


def test_integracao_gate_antes_do_envio():
    from pathlib import Path

    codigo = Path("pipeline_rss.py").read_text(encoding="utf-8")

    assert codigo.index("validacao = validar_saida(") < codigo.index(
        "wp_result = publicar_no_wordpress("
    )
