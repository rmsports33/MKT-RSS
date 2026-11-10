"""MDA-informed editorial voice guidance; no model, network, persona or publication.

The MDA AUTO academic archive is process documentation, not a second writer.
This adapter supplies brief-bound editorial lenses and non-approving diagnostics
to the existing MKT-RSS writer and critic. Editorial DNA remains canonical.
"""
import re

# Lenses are ways of reasoning about evidence, never simulated people.
LENSES = {
    "documental": {
        "name": "investigativo-documental",
        "opening": "Separe o fato documentado da promessa, da inferência e do que ainda falta apurar.",
        "development": "Confronte versões ou documentos apenas quando houver divergência sustentada.",
        "ending": "Mostre o próximo fato verificável que mudará o entendimento do caso.",
    },
    "analitica": {
        "name": "analítico-crítica",
        "opening": "Apresente a pergunta relevante e o alcance das evidências disponíveis.",
        "development": "Relacione mecanismo, contexto, consequências e alternativas sem inventar consenso.",
        "ending": "Conclua com interpretação proporcional às fontes e ressalvas decisivas.",
    },
    "didatica": {
        "name": "didático-prática",
        "opening": "Comece pelo sintoma ou decisão concreta do leitor, não pela ordem de um manual.",
        "development": "Distinga cenários, consequências e passos reversíveis apoiados por documentação.",
        "ending": "Indique quando a orientação vale e quando exige consulta ou verificação adicional.",
    },
    "comparativa": {
        "name": "comparativo-decisória",
        "opening": "Defina os critérios que realmente separam as alternativas para o leitor.",
        "development": "Compare por cenário e trade-off, distinguindo especificação de teste real.",
        "ending": "Ofereça decisão condicional com limites, sem inventar preços nem experiência própria.",
    },
    "cientifica": {
        "name": "científico-explicativa",
        "opening": "Apresente a pergunta, o estudo e o alcance da amostra antes do efeito alegado.",
        "development": "Distinga correlação, mecanismo, hipótese, resultado e possíveis interpretações.",
        "ending": "Explique o que o estudo permite concluir e o que permanece incerto.",
    },
    "factual": {
        "name": "factual-concisa",
        "opening": "Dê o fato verificado e sua relevância concreta em primeiro lugar.",
        "development": "Acrescente somente o contexto necessário para entender a novidade.",
        "ending": "Pare quando não houver novo fato; não force conclusão decorativa.",
    },
}

DEFAULT_LENSES = {
    "noticia": "documental",
    "guia": "didatica",
    "analise": "analitica",
    "comparativo": "comparativa",
    "review": "comparativa",
    "nota_breve": "factual",
}

_RESEARCH_TERMS = ("pesquisa", "estudo", "experimento", "levantamento científico")
_GENERIC_CONNECTORS = (
    "além disso", "nesse sentido", "dessa forma", "portanto", "em suma",
    "por conseguinte", "outrossim", "em conclusão", "por fim",
)


def editorial_voice_plan(brief, *, preferred_lens=None):
    """Return an advisory plan tied to the unchanged canonical six-field brief.

    A manually selected lens must be on the allowlist; no new persona or
    factual assertions can be provided through an arbitrary prompt field.
    """
    from mkt_flow_p0.editorial_substance import normalize_brief, brief_hash
    brief = normalize_brief(brief)
    if preferred_lens is None:
        lens = DEFAULT_LENSES[brief["genre"]]
        # The scientific lens is relevant when the actual angle is a study,
        # not whenever an article casually contains the word "science".
        if brief["genre"] == "analise" and any(
            term in brief["angle"].casefold() for term in _RESEARCH_TERMS
        ):
            lens = "cientifica"
    else:
        if preferred_lens not in LENSES:
            raise ValueError("lente editorial desconhecida")
        lens = preferred_lens
    spec = LENSES[lens]
    return {
        "schema": "conexo-editorial-voice-plan/1",
        "brief_sha256": brief_hash(brief),
        "genre": brief["genre"],
        "lens": lens,
        "lens_name": spec["name"],
        "opening": spec["opening"],
        "development": spec["development"],
        "ending": spec["ending"],
        "status": "ADVISORY_NOT_APPLIED_OR_APPROVED",
        "factual_approval": False,
        "publication_authorized": False,
    }


def writing_voice_guidance(brief):
    """Compact instruction used in an existing generation call; zero extra calls."""
    plan = editorial_voice_plan(brief)
    return (
        "\nLENTE EDITORIAL ADAPTATIVA (MDA AUTO; NÃO é persona fictícia nem outro autor): "
        + plan["lens_name"] + ". "
        + "Abertura: " + plan["opening"] + " "
        + "Progressão: " + plan["development"] + " "
        + "Desfecho: " + plan["ending"] + " "
        + "Cada parte deve acrescentar evidência, distinção, consequência ou orientação. "
        + "Não faça uma seção por movimento obrigatório, não fabrique contraste "
        + "nem varie frases artificialmente. Preserve limites, exceções e "
        + "a correspondência entre afirmação e fonte; quando faltar prova, marque pendência. "
        + "Corte paráfrases e fechamentos decorativos sem cortar raciocínio. "
        + "O DNA ConexoTech e a revisão humana por versão continuam prevalecendo.\n"
    )


def surface_style_signals(markdown):
    """Only identify review leads, never infer semantic quality or grant PASS.

    Detects visibly mechanical paragraph starts. Semantic repetition, causal
    errors, invented observations and conclusions require substantive review.
    """
    if not isinstance(markdown, str):
        raise ValueError("texto inválido para triagem de estilo")
    paragraphs = []
    for paragraph in re.split(r"\n\s*\n", markdown):
        normalized = re.sub(r"\s+", " ", paragraph).strip()
        if normalized.startswith(("#", "|", "!", "- ", "* ")):
            continue
        if len(normalized.split()) >= 8:
            paragraphs.append(normalized.casefold())
    lead_count = sum(
        1 for paragraph in paragraphs
        if any(
            paragraph.startswith(word + " ") or paragraph.startswith(word + ",")
            for word in _GENERIC_CONNECTORS
        )
    )
    signals = []
    if lead_count >= 3:
        signals.append("possiveis_conectivos_mecanicos")
    if paragraphs and any(
        paragraphs[-1].startswith(word + " ") or paragraphs[-1].startswith(word + ",")
        for word in ("em suma", "em conclusão", "por fim")
    ):
        signals.append("revisar_funcao_do_fechamento")
    return {
        "scope": "triagem_superficial_nao_semantica",
        "paragraphs_considered": len(paragraphs),
        "signals": signals,
        "factual_approval": False,
        "publication_authorized": False,
    }
