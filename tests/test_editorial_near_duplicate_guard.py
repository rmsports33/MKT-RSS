"""Regression: optimistic LLM scores must not hide lightly rewritten filler."""
import re

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
    # Every sentence and every paragraph is unique: the prior exact-match
    # detector would pass this superficially rewritten padding.
    base_sentences = [
        "O leitor precisa verificar a configuração no aparelho antes de decidir, porque as escolhas produzem consequências diferentes, e o texto deve mostrar critérios específicos antes de recomendar qualquer intervenção na experiência de escrita",
        "É necessário explicar o impacto concreto e os limites da documentação sem prometer um resultado que não foi verificado pela redação, especialmente quando o sistema e o idioma podem mudar o comportamento observado",
        "A comparação útil deve distinguir uma mudança pontual de uma mudança geral, explicar o custo de perder sugestões e apresentar uma forma reversível de conferir o ajuste sem simular teste próprio",
        "A conclusão deve sintetizar a decisão que o leitor realmente enfrenta, dar a ressalva correspondente e evitar repetir simplesmente o passo a passo da documentação ou encerrar com frases vazias",
    ]
    paragraphs = [
        ". ".join(f"{sentence} no cenário {i}" for sentence in base_sentences) + "."
        for i in range(8)
    ]
    article = "\n\n".join(paragraphs)
    long_sentences = [
        sentence.strip().casefold() for sentence in re.split(r"[.!?]\s+", article)
        if len(sentence.split()) > 6
    ]
    assert len(set(paragraphs)) == len(paragraphs)
    assert len(set(long_sentences)) == len(long_sentences)
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
