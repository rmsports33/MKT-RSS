"""Regressions from actual 11/11 MDA A/B issues, without storing private articles."""
import json
from types import SimpleNamespace

import pytest

from mkt_flow_p0.editorial_voice_adapter import (
    editorial_placeholder_signals, writing_voice_guidance,
)
from mkt_flow_p0.editorial_substance import assess_substance
from mkt_flow_p0.rewriter import reescrever_materia


def briefing(genre="analise"):
    return {
        "genre": genre,
        "reader": "Leitores brasileiros que querem reconhecer consequências tecnológicas.",
        "need": "Compreender limitações sem inventar testes, preços ou datas comerciais.",
        "angle": "Separar documento de certificação, hipótese e conclusão confiável.",
        "contribution": "Explicar implicações práticas e dar critérios com fontes.",
        "limits": "Nenhum teste próprio ou oferta comercial comprovada.",
    }


@pytest.mark.parametrize("example", [
    "Novo DLSS 5 foi disponibilizado em setembro no *[jogo X]*.",
    "O nome do produto será [inserir modelo] após apuração.",
    "A imagem será exibida em [imagem X].",
    "O valor é [preço a confirmar] no mercado brasileiro.",
])
def test_unresolved_editorial_markers_are_not_accepted_as_finished_articles(example):
    signals = editorial_placeholder_signals(example)
    assert signals["signals"] == ["marcador_editorial_nao_resolvido"]
    assert signals["factual_approval"] is False
    status = assess_substance(example, briefing())
    assert "marcador_editorial_nao_resolvido" in status["pendencias"]
    assert status["status"] == "PENDING"
    assert status["publication_authorized"] is False


@pytest.mark.parametrize("example", [
    "Este texto segue o briefing editorial e resume as fontes originais.",
    "Como modelo de linguagem, eu não posso verificar o anúncio.",
])
def test_metatextual_generation_disclaimers_remain_editorial_pending(example):
    result = editorial_placeholder_signals(example)
    assert result["signals"] == ["metatexto_de_producao_no_artigo"]


def test_never_break_normal_markdown_citations_code_or_controls():
    text = (
        "Confira o [site da Apple](https://support.apple.com/pt-br/104995). "
        "O [artigo 1] é uma referência numerada. O controle do teclado foi ajustado.\n\n"
        "```text\n[jogo X] é exemplo proposital em código, não um manuscrito.\n```\n"
        "Texto completo sem marcadores de produção."
    )
    assert editorial_placeholder_signals(text)["signals"] == []


def test_writer_names_uncertainties_without_inventing_product_or_sale():
    analysis = writing_voice_guidance(briefing())
    news = writing_voice_guidance(briefing("noticia"))
    assert "[jogo X]" in analysis and "omita" in analysis.casefold()
    assert "homologa" in news.casefold()
    assert "disponibilidade comercial" in news
    assert "não" in news.casefold()


def test_rewriter_rejects_placeholder_even_with_long_provider_output(monkeypatch):
    import mkt_flow_p0.rewriter as rewriter
    calls = []

    def fake_create(**kwargs):
        calls.append(kwargs)
        body = ("O leitor precisa avaliar os limites e as condições antes de agir. " * 25
                + "No laboratório, a empresa citou *[jogo X]* como exemplo. "
                + "O texto não confirma o resultado por conta própria. " * 20)
        return SimpleNamespace(
            choices=[SimpleNamespace(
                finish_reason="stop",
                message=SimpleNamespace(content=json.dumps({
                    "titulo_seo": "Tecnologia e decisões do consumidor",
                    "meta_description": "Análise genérica e incompleta não autorizada para publicar, só para teste.",
                    "slug": "tecnologia-decisoes-consumidor",
                    "tags": ["tecnologia"],
                    "texto_markdown": body,
                }, ensure_ascii=False)),
            )],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=700),
        )

    monkeypatch.setattr(rewriter, "_get_client", lambda: (
        SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))),
        "",
    ))
    monkeypatch.setattr(rewriter, "_modelo", lambda: "model-ci-sintetico")
    src = "Manual e documentos técnicos precisam de interpretação verificável. " * 30
    result = reescrever_materia("Análise", src, editorial_brief=briefing())
    assert len(calls) == 1
    assert result["erro"].startswith("Reescrita contém")
    assert result["pendencias"] == ["marcador_editorial_nao_resolvido"]
    assert "texto_markdown" not in result


def test_no_automated_score_can_turn_placeholder_into_ready():
    sample = ("A interpretação depende da fonte e das limitações do estudo. " * 14
              + "O jogo foi apresentado em [jogo X] sem identificação. ")
    review = {
        "method": "assisted", "reviewer": "fixture-reviewer",
        "content_sha256": __import__("hashlib").sha256(sample.encode()).hexdigest(),
        "brief_sha256": __import__("mkt_flow_p0.editorial_substance",
                                    fromlist=["brief_hash"]).brief_hash(briefing()),
        "criteria": {
            key: {
                "score": 4,
                "reason": "Revisão sintética para provar que a nota não supera defeito estrutural.",
                "excerpt": sample[:100],
            }
            for key in ("reader_need", "editorial_angle", "decision_support", "voice", "source_limits")
        },
    }
    result = assess_substance(sample, briefing(), review)
    assert result["review_valid"] is True
    assert "marcador_editorial_nao_resolvido" in result["pendencias"]
    assert result["status"] == "PENDING"
    assert result["factual_approval"] is False
    assert result["publication_authorized"] is False
