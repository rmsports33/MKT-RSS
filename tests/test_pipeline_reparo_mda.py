"""Reparo de HTML e diagnóstico MDA conectados ao pipeline. Offline."""
from unittest.mock import patch

import pipeline_rss as p
from mkt_flow_p0.linguagem_validator import (
    ErroLinguagem, RelatorioLinguagem, bloqueios_para_rascunho,
)


def test_reparo_aplicado_quando_ha_fragmentacao():
    quebrado = "<ol><li>Um</li></ol>\n<ol><li>Dois</li></ol>"
    html, rel = p._reparar_html_fragmentado(quebrado)
    assert rel["aplicado"] is True
    assert rel["fragmentacoes_detectadas"] > 0
    assert html.count("<ol>") == 1
    assert rel["autoriza_publicacao"] is False


def test_sem_fragmentacao_nao_altera_html():
    bom = "<p>Primeira frase.</p>\n<p>Segunda frase.</p>"
    html, rel = p._reparar_html_fragmentado(bom)
    assert html == bom
    assert rel["aplicado"] is False
    assert rel["motivo"] == "sem_fragmentacao_detectada"


def test_falha_no_reparo_preserva_html():
    with patch("mkt_flow_p0.html_paragrafos.listas_seguidas",
               side_effect=RuntimeError("boom")):
        html, rel = p._reparar_html_fragmentado("<p>x</p>")
    assert html == "<p>x</p>"
    assert rel["aplicado"] is False
    assert rel["erro"] == "RuntimeError"


def test_auditoria_mda_e_diagnostica():
    out = p._auditoria_voz_mda("Texto de teste com conteúdo suficiente.", None)
    assert out["executado"] is True
    assert out["avaliacao_humana"] is False
    assert out["autoriza_publicacao"] is False
    assert out["relatorio"]["factual_approval"] is False


def test_bloqueio_apenas_critico_e_estrutural():
    rel = RelatorioLinguagem(texto="x", erros=[
        ErroLinguagem("C1", "tipografia", "crítica", "x", 0, "critico"),
        ErroLinguagem("H1", "html", "alta", "", 0, "lista fragmentada"),
        ErroLinguagem("T1", "tipografia", "baixa", "x", 0, "aspas retas"),
        ErroLinguagem("G1", "gramática", "alta", "x", 0, "heuristica"),
    ])
    codigos = [b["codigo"] for b in bloqueios_para_rascunho(rel)]
    assert codigos == ["C1", "H1"]


def test_bloqueios_aceita_dict_e_nao_bloqueia_sem_erros():
    assert bloqueios_para_rascunho({"erros": []}) == []
    rel = RelatorioLinguagem(texto="x", erros=[
        ErroLinguagem("A1", "caractere", "alta", "x", 0, "cirilico")])
    assert bloqueios_para_rascunho({"erros": [rel.erros[0].__dict__]})[0]["codigo"] == "A1"


def test_auditoria_mda_falha_fechada():
    with patch("mkt_flow_p0.linguagem_validator.verificar_voz_editorial_mda",
               side_effect=ValueError("brief invalido")):
        out = p._auditoria_voz_mda("texto", {"genre": "noticia"})
    assert out["executado"] is False
    assert out["autoriza_publicacao"] is False
