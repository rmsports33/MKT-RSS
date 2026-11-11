"""No-cost MDA argument-path regressions; no publication or actual reviewer approval."""
import json
from types import SimpleNamespace

import pytest

from mkt_flow_p0.editorial_substance import (
    CRITERIA, assess_substance, brief_hash, writing_instruction,
)
from mkt_flow_p0.editorial_voice_adapter import (
    ARGUMENT_MOVES, argumentation_review_questions, editorial_argument_plan,
    writing_voice_guidance,
)
from mkt_flow_p0.editorial_development import review_with_provider
from mkt_flow_p0.rewriter import montar_prompt


def brief(genre="comparativo", angle="Comparar critérios verificáveis por perfil de leitor."):
    return {
        "genre": genre,
        "reader": "Leitor brasileiro que quer entender uma escolha de tecnologia.",
        "need": "Descobrir vantagens e limitações sem testes ou preços inventados.",
        "angle": angle,
        "contribution": "Explicar consequências práticas e limites dos dados disponíveis.",
        "limits": "Sem teste próprio, preços atuais, imagens ou desempenho medido.",
    }


@pytest.mark.parametrize("genre,expected", [
    ("noticia", "documental"),
    ("guia", "didatica"),
    ("analise", "analitica"),
    ("comparativo", "comparativa"),
    ("review", "comparativa"),
    ("nota_breve", "factual"),
])
def test_argument_path_is_genre_specific_and_bound_to_unchanged_brief(genre, expected):
    source = brief(genre)
    plan = editorial_argument_plan(source)
    assert plan["lens"] == expected
    assert plan["brief_sha256"] == brief_hash(source)
    assert set(plan["moves"]) == {"thesis", "evidence", "consequence", "tradeoff", "closing"}
    assert all(isinstance(item, str) and len(item) > 25 for item in plan["moves"].values())
    assert plan["factual_approval"] is False
    assert plan["publication_authorized"] is False
    assert plan["status"] == "ADVISORY_NOT_APPLIED_OR_APPROVED"
    assert set(ARGUMENT_MOVES) == {
        "documental", "analitica", "didatica", "comparativa", "cientifica", "factual",
    }


def test_analise_de_pesquisa_uses_scientific_argument_and_rejects_causality_shortcut():
    plan = editorial_argument_plan(brief("analise", "Analisar pesquisa e amostra de 1.799 participantes."))
    assert plan["lens"] == "cientifica"
    assert "correlação" in plan["moves"]["tradeoff"]
    assert "amostra" in plan["moves"]["evidence"]


def test_existing_writer_gets_argumentation_without_new_executor_or_legacy_control_change():
    source = brief()
    treatment = writing_instruction(source)
    control = writing_instruction(source, voice_variant="control")
    guidance = writing_voice_guidance(source)
    prompt = montar_prompt(
        "Escolher um smartphone", "A ficha técnica descreve opções e limites. " * 25,
        fonte_nome="Fonte oficial de teste", editorial_brief=source,
    )
    assert treatment == control + guidance
    assert "MOVIMENTO ARGUMENTATIVO" in treatment
    assert "Tese:" in treatment and "Prova:" in treatment
    assert "Consequência:" in treatment and "Contrapeso:" in treatment
    assert "Veredito/limite:" in treatment
    assert "Preço e disponibilidade somente com fonte, data, mercado e variante." in prompt
    assert "testes, fotografias, benchmarks" in prompt
    assert "MOVIMENTO ARGUMENTATIVO" not in control
    assert "Canaltech" not in prompt  # Learn editorial reasoning, do not imitate a named outlet.


def test_news_and_brief_do_not_force_purchase_recommendation_or_canned_conclusion():
    news = writing_voice_guidance(brief("noticia"))
    short = writing_voice_guidance(brief("nota_breve"))
    assert "não force recomendação de compra" in news
    assert "sem veredito ou fechamento decorativo" in short
    assert "não invente conclusão forte" in news.casefold()


def test_reviewer_questions_remain_advisory_and_genre_bound():
    review = argumentation_review_questions(brief("guia"))
    assert [x["move"] for x in review] == [
        "thesis", "evidence", "consequence", "tradeoff", "closing",
    ]
    assert "reversível" in review[3]["genre_expectation"]
    assert all("review_question" in x and "genre_expectation" in x for x in review)


def test_existing_assisted_review_receives_argument_questions_with_same_provider_call(monkeypatch):
    import mkt_flow_p0.rewriter as rewriter
    captured = []
    markdown = (
        "A escolha exige distinguir a especificação do uso medido e das limitações. "
        "O comprador deve conferir dados de versão, documentação e condições "
        "antes de tirar uma conclusão, porque diferentes cenários têm riscos distintos. "
    ) * 3
    excerpt = markdown[:170]
    criteria = {
        key: {
            "score": 3, "reason": "Avaliação fictícia somente para teste offline de transporte, sem aceite.",
            "excerpt": excerpt,
        }
        for key in CRITERIA
    }

    def fake_create(**kwargs):
        captured.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(
            finish_reason="stop",
            message=SimpleNamespace(content=json.dumps({"criteria": criteria}, ensure_ascii=False))
        )])

    monkeypatch.setattr(rewriter, "_get_client", lambda: (
        SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))),
        None,
    ))
    monkeypatch.setattr(rewriter, "_modelo", lambda: "fixture-model")
    monkeypatch.setattr(rewriter, "_parse_json_resposta", json.loads)
    report = review_with_provider(markdown, brief())
    assert len(captured) == 1  # no extra provider call
    assert captured[0]["temperature"] == 0
    sys_prompt = captured[0]["messages"][0]["content"]
    payload = json.loads(captured[0]["messages"][1]["content"])
    assert "tese→prova→consequência" in sys_prompt
    assert "teste próprio" in sys_prompt
    assert len(payload["non_approving_argumentation_questions"]) == 5
    assert payload["brief"] == brief()
    assert payload["article"] == markdown
    assert report["method"] == "assisted"
    assert assess_substance(markdown, brief(), report)["review_valid"] is True
    assert assess_substance(markdown, brief(), report)["factual_approval"] is False
    assert assess_substance(markdown, brief(), report)["publication_authorized"] is False
