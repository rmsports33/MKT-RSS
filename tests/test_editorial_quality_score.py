"""Avaliador editorial 0-100 baseado no contrato unico. Sem rede."""
import json
from pathlib import Path

import pytest

from mkt_flow_p0 import editorial_import
from mkt_flow_p0.editorial_quality_score import (
    avaliar_artigo, carregar_contrato, padrao_canaltech,
)
from mkt_flow_p0.editorial_substance import brief_hash, content_hash, normalize_brief

BRIEF = {
    "genre": "analise",
    "reader": "Leitor brasileiro de tecnologia que quer entender consumo de energia.",
    "need": "Entender quando eficiência reduz ou aumenta o gasto total.",
    "angle": "Explicar o paradoxo com limite explícito das fontes.",
    "contribution": "Critérios para ler manchetes sem transformar hipótese em fato.",
    "limits": "Não inventar contexto brasileiro, preços ou testes próprios.",
}
TEXTO = "\n\n".join([
    "Para quem acompanha tecnologia, a pergunta é se eficiência reduz gasto. "
    "A tese é que depende da elasticidade da demanda e da política adotada.",
    "Em 1865, Jevons observou que o motor mais eficiente ampliou o consumo de carvão. "
    "Segundo a literatura, o efeito rebound pode anular a economia inicial.",
    "Na prática, isso afeta decisões de consumo. Mas há limites: os estudos divergem "
    "sobre a magnitude do efeito, e preços mudam conforme data e mercado.",
    "Para quem decide, o veredito é condicional: eficiência sozinha não garante economia. "
    "Em síntese, a conclusão depende da política adotada.",
])
FONTES = {"sources": [
    {"name": "Fonte A", "url": "https://example.org/a", "facts": ["Eficiência pode aumentar o uso total."]},
    {"name": "Fonte B", "url": "https://example.com/b", "facts": ["Rebound depende da elasticidade."]},
]}


def revisao_valida(texto=TEXTO, brief=BRIEF):
    return {
        "method": "assisted", "reviewer": "groq:teste",
        "content_sha256": content_hash(texto),
        "brief_sha256": brief_hash(normalize_brief(brief)),
        "criteria": {
            nome: {"score": 4, "reason": "Justificativa com evidência literal no texto para revisão.",
                   "excerpt": "eficiência sozinha não garante economia. Em síntese, a conclusão depende da política adotada."}
            for nome in ("reader_need", "editorial_angle", "decision_support", "voice", "source_limits")
        },
    }


def test_contrato_carrega_e_valida_hash():
    c = carregar_contrato()
    assert len(c["contract_sha256"]) == 64
    assert c["reference_pattern"]["source_doc"].endswith("EDITORIAL_REFERENCE_CANALTECH_S26FE_20261110.md")
    assert c["brazilian_focus"]["never_invent"] is True


def test_nota_0_a_100_com_revisao_valida():
    r = avaliar_artigo(TEXTO, brief=BRIEF, review=revisao_valida(),
                       sources=FONTES, title="Título", meta="Descrição com mais de sessenta caracteres para seo.",
                       review_status="PROMPT_APPLIED", image_rights=True)
    assert 0 <= r["nota"] <= 100
    assert r["nota_assistida"] == 100
    assert r["estado_revisao"] == "valida"
    assert r["publication_authorized"] is False
    assert r["factual_approval"] is False


def test_fonte_unica_limita_nota_a_69():
    uma = {"sources": [FONTES["sources"][0]]}
    r = avaliar_artigo(TEXTO, brief=BRIEF, sources=uma, genero="analise",
                       title="T", meta="M" * 70, review_status="PROMPT_APPLIED")
    assert "multifonte" in r["bloqueios"]
    assert r["nota"] <= 69


def test_contexto_brasileiro_inventado_bloqueia():
    texto = TEXTO + "\n\nNo Brasil, o consumidor paga reais acima da média."
    r = avaliar_artigo(texto, brief=BRIEF, sources=FONTES, genero="analise",
                       title="T", meta="M" * 70, review_status="PROMPT_APPLIED")
    assert "publico_brasileiro" in r["bloqueios"]


def test_limite_brasileiro_nao_e_contexto_inventado():
    texto = TEXTO + "\n\nNão há dados públicos brasileiros sobre esse efeito."
    r = avaliar_artigo(texto, brief=BRIEF, sources=FONTES, genero="analise",
                       title="T", meta="M" * 70, review_status="PROMPT_APPLIED")
    assert "publico_brasileiro" not in r["bloqueios"]


def test_padrao_canaltech_compara_sem_copiar():
    p = padrao_canaltech(TEXTO)
    assert p["checagens"]["tese_condicional"] is True
    assert p["checagens"]["veredito_proporcional"] is True
    assert 0 <= p["cobertura"] <= 1


def test_import_gera_recibo_e_resumo(tmp_path):
    payload = {
        "source_url": "https://example.org/fonte",
        "source_name": "Fonte",
        "research": FONTES,
        "editorial_brief": BRIEF,
        "editorial_substance_review": revisao_valida(),
        "article": {"titulo_seo": "Título", "meta_description": "M" * 70,
                    "slug": "teste", "texto_markdown": TEXTO},
    }
    payload["article"]["texto_markdown"] = TEXTO + "\n\n" + (
        "A literatura analisa efeitos indiretos sobre o consumo total de energia. "
        "Cada seção acrescenta uma consequência prática para quem decide. ") * 40
    caminho = tmp_path / "entrada.json"
    caminho.write_text(json.dumps(payload), encoding="utf-8")
    resultado = editorial_import.processar_artigo_importado(
        payload, tmp_path / "saida", offline=True, genero="analise")
    assert "quality_score" in resultado
    assert (tmp_path / "saida" / "quality-receipt.json").exists()
    resumo = editorial_import.resumo_execucao(resultado)
    assert "quality_score" in resumo

def test_links_internos_acima_da_recomendacao_sao_aviso_nao_bloqueio():
    links = "\n\n" + " ".join(
        f"[Matéria {i}](https://conexotech.com.br/materia-{i}/)" for i in range(4)
    )
    r = avaliar_artigo(
        TEXTO + links, brief=BRIEF, sources=FONTES, genero="analise",
        title="Título", meta="M" * 70, image_rights=True,
        review_status="PROMPT_APPLIED",
    )
    link_check = next(c for c in r["checks"] if c["id"] == "links_internos")
    assert link_check["status"] == "FAIL"
    assert link_check["severidade"] == "warning"
    assert "links_internos" not in r["bloqueios"]
    assert "links_internos" in r["pendencias"]


def test_mapa_canaltech_nao_penaliza_noticia_ou_analise():
    for genre in ("noticia", "analise", "guia", "nota_breve"):
        r = avaliar_artigo(
            TEXTO, brief={**BRIEF, "genre": genre}, sources=FONTES, genero=genre,
            title="Título", meta="M" * 70, image_rights=True,
            review_status="PROMPT_APPLIED",
        )
        assert r["padrao_canaltech"]["aplicavel"] is False
        assert r["padrao_canaltech"]["cobertura"] is None
        # O texto curto gera apenas o aviso de tamanho (5 pontos).
        assert r["nota_estrutural"] == 95


def test_mapa_canaltech_aplica_apenas_a_comparativos_e_reviews():
    assert padrao_canaltech(TEXTO, genero="comparativo")["aplicavel"] is True
    assert padrao_canaltech(TEXTO, genero="review")["aplicavel"] is True
    assert padrao_canaltech(TEXTO, genero="noticia")["aplicavel"] is False
    # Não mencionar preço ou estoque não pode produzir uma falha artificial.
    assert "preco_datado" not in padrao_canaltech(TEXTO, genero="review")["checagens"]

