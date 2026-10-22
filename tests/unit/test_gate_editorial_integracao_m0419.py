from unittest.mock import patch

from mkt_flow_p0.gate_editorial_pos_ia import validar_saida


def test_gate_identifica_artigo_suspeito():
    fonte = "A empresa anunciou um novo produto."
    artigo = "Avaliamos o produto e encontramos 512 GB."
    resultado = validar_saida(fonte, artigo)
    assert resultado["veredito"] == "BLOQUEADO"


def test_pipeline_contem_gate_antes_do_wordpress():
    from pathlib import Path

    codigo = Path("pipeline_rss.py").read_text(encoding="utf-8")
    assert codigo.index("validacao = validar_saida(") < codigo.index(
        "wp_result = publicar_no_wordpress("
    )
