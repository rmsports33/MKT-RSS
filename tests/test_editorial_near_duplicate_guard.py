"""Regression: optimistic LLM scores must not hide lightly rewritten filler."""
from mkt_flow_p0.editorial_substance import assess_substance, brief_hash, content_hash

BRIEF = {
    "genre": "guia",
    "reader": "Leitor brasileiro buscando orientação técnica prática e verificável.",
    "need": "Distinguir as escolhas possíveis antes de mudar a configuração do aparelho.",
    "angle": "Comparar cenários e consequências, sem reproduzir sequência de manual.",
    "contribution": "Explicar o custo e a reversibilidade de cada decisão técnica.",
    "limits": "Não houve teste próprio nem verificação de versões específicas do sistema.",
}
CORE = (
    "O leitor precisa verificar a configuração no aparelho antes de decidir, porque "
    "as escolhas produzem consequências diferentes. É necessário explicar o impacto "
    "concreto e os limites da documentação sem prometer um resultado que não foi "
    "verificado pela redação. "
)


def _optimistic_review(article):
    excerpts = [p for p in article.split("\n\n") if len(p) > 60]
    return {
        "method": "assisted",
        "reviewer": "fixture-automated-critic",
        "content_sha256": content_hash(article),
        "brief_sha256": brief_hash(BRIEF),
        "criteria": {
            name: {
                "score": 4,
                "reason": "Parecer otimista de teste, não é avaliação independente nem humana.",
                "excerpt": excerpts[0],
            }
            for name in ("reader_need", "editorial_angle", "decision_support",
                         "voice", "source_limits")
        },
    }


def test_paraphrased_boilerplate_fails_even_with_optimistic_review():
    paragraphs = [
        CORE + f" No cenário {i}, mudamos somente um pequeno detalhe da recomendação."
        for i in range(8)
    ]
    article = "\n\n".join(paragraphs)
    assessment = assess_substance(article, BRIEF, _optimistic_review(article))
    assert assessment["review_valid"]
    assert "repeticao_substantiva" in assessment["pendencias"]
    assert assessment["status"] == "PENDING"


def test_distinct_long_paragraphs_do_not_trigger_repetition_guard():
    paragraphs = [
        " ".join(f"conceito{i}_dado{j}" for j in range(35))
        for i in range(8)
    ]
    assessment = assess_substance("\n\n".join(paragraphs))
    assert "repeticao_substantiva" not in assessment["pendencias"]
