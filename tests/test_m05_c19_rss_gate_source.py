"""Regressao estatico-conservadora do bloqueio C19 (sem rede/LLM/WP)."""
from pathlib import Path


def test_rss_nao_envia_pass_literal_antes_do_bloqueio_pos_ia():
    import ast
    source = (Path(__file__).resolve().parents[1] / "pipeline_rss.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    chamadas_wp = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "publicar_no_wordpress"
    ]
    assert not chamadas_wp
    assert '"motivo": "gate_factual_pos_ia_nao_integrado"' in source
    assert '"escreveu": False' in source


def test_rss_reusa_gate_pos_ia_sem_tratar_sem_alertas_como_pass():
    source = (Path(__file__).resolve().parents[1] / "pipeline_rss.py").read_text(encoding="utf-8")
    assert "from mkt_flow_p0.gate_editorial_pos_ia import validar_saida" in source
    assert 'validar_saida(ext["texto"], rw["texto_markdown"])' in source
    assert 'verificacao_factual = "NAO_VERIFICADO"' in source
    assert '"auditoria_pos_ia": auditoria_pos_ia' in source


def test_gate_pos_ia_bloqueia_numero_inventado_e_alegacao_de_teste():
    from mkt_flow_p0.gate_editorial_pos_ia import validar_saida

    fonte = "O fabricante informou bateria de 5000 mAh e tela OLED."
    inventado = validar_saida(fonte, "A bateria tem 9000 mAh.")
    assert inventado["veredito"] == "BLOQUEADO"
    assert "numeros_sem_correspondencia_na_fonte" in inventado["motivos"]

    falso_teste = validar_saida(fonte, "Testamos o aparelho em nosso laboratorio.")
    assert falso_teste["veredito"] == "BLOQUEADO"
    assert "alegacao_de_teste_proprio" in falso_teste["motivos"]


def test_sem_alertas_nao_e_prova_factual():
    from mkt_flow_p0.gate_editorial_pos_ia import validar_saida

    resultado = validar_saida("A empresa anunciou uma tela OLED.", "A empresa anunciou uma tela OLED.")
    assert resultado["veredito"] == "SEM_ALERTAS"
    assert resultado["veredito"] != "PASS"


def test_rss_avalia_contrato_sem_liberar_wordpress():
    source = (Path(__file__).resolve().parents[1] / "pipeline_rss.py").read_text(encoding="utf-8")
    assert 'avaliar_evidencias(rw.get("contrato_editorial"))' in source
    assert '"auditoria_evidencias": auditoria_evidencias' in source
    assert source.index('avaliar_evidencias(rw.get("contrato_editorial"))') < source.index('gate_factual_pos_ia_nao_integrado')
    assert 'verificacao_factual = "NAO_VERIFICADO"' in source
