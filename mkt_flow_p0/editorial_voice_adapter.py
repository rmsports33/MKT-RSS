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


# A thesis-to-consequence pathway, never a template or invented reporting.
# Adapted as a general editorial practice; no third-party text is reproduced.
ARGUMENT_MOVES = {
    "documental": {
        "thesis": "Explique a novidade comprovada e por que importa agora ao público.",
        "evidence": "Separe documento primário, declaração interessada e lacuna verificável.",
        "consequence": "Mostre o que muda na prática e o que ainda NÃO está disponível.",
        "tradeoff": "Registre expectativas divergentes somente se houver fontes para ambas.",
        "closing": "Indique o próximo fato verificável; não force recomendação de compra.",
    },
    "analitica": {
        "thesis": "Formule uma interpretação provisória e testável para o problema do leitor.",
        "evidence": "Dê a base documental e indique a força ou a amostra de cada evidência.",
        "consequence": "Explique o que a conclusão muda em cenários e públicos distintos.",
        "tradeoff": "Considere interpretações concorrentes e causalidade não demonstrada.",
        "closing": "Ofereça síntese condicional, com limites e fatos capazes de revisá-la.",
    },
    "didatica": {
        "thesis": "Explique qual decisão ou sintoma concreto o guia ajuda a resolver.",
        "evidence": "Fundamente cada instrução na versão e documentação adequadas.",
        "consequence": "Para cada passo, explicite o efeito esperado e o que pode ser perdido.",
        "tradeoff": "Prefira correção reversível antes de medidas amplas ou destrutivas.",
        "closing": "Indique quando funciona, quando não funciona e quando pedir suporte.",
    },
    "comparativa": {
        "thesis": "Indique quais diferenças realmente decidem a escolha do leitor.",
        "evidence": "Diferencie ficha técnica, medição própria comprovada e teste de terceiros.",
        "consequence": "Relacione atributos a consequências e perfis concretos de uso.",
        "tradeoff": "Pese vantagens e limitações sem inventar experiência, preços ou vencedores.",
        "closing": "Conclua para quem e sob quais condições cada opção faz sentido.",
    },
    "cientifica": {
        "thesis": "Formule a pergunta investigada sem antecipar uma conclusão definitiva.",
        "evidence": "Identifique desenho, amostra, representatividade e resultados observados.",
        "consequence": "Traduza o significado potencial dos resultados sem extrapolação.",
        "tradeoff": "Separe hipótese, correlação, causalidade e limites metodológicos.",
        "closing": "Explique o que já se sabe e qual evidência mudaria o julgamento.",
    },
    "factual": {
        "thesis": "Dê o fato verificável e sua consequência direta na abertura.",
        "evidence": "Inclua só a atribuição e a confirmação suficientes para uma nota breve.",
        "consequence": "Mostre o impacto conhecido sem inflar uma possibilidade futura.",
        "tradeoff": "Sinalize a lacuna decisiva, sem criar falsa controvérsia.",
        "closing": "Termine no último fato útil, sem veredito ou fechamento decorativo.",
    },
}


def editorial_argument_plan(brief):
    """Advisory argumentative movement plan, not a score or approval receipt.

    Derives only from existing allowlisted lenses and immutable six-field brief.
    """
    voice = editorial_voice_plan(brief)
    return {
        "schema": "conexo-editorial-argument-plan/1",
        "brief_sha256": voice["brief_sha256"],
        "genre": voice["genre"],
        "lens": voice["lens"],
        "moves": dict(ARGUMENT_MOVES[voice["lens"]]),
        "status": "ADVISORY_NOT_APPLIED_OR_APPROVED",
        "factual_approval": False,
        "publication_authorized": False,
    }


def argumentation_review_questions(brief):
    """Same existing critic call; questions supplement, never replace, its rubric."""
    plan = editorial_argument_plan(brief)
    probes = {
        "thesis": "A abertura traz questão/tese verificável sem inventar certeza?",
        "evidence": "Fontes e testes têm proveniência, data e alcance adequados?",
        "consequence": "Cada fato relevante produz consequência concreta para o leitor?",
        "tradeoff": "Limitações, alternativas e contraexemplos estão contextualizados?",
        "closing": "O fechamento responde à tese nos limites das evidências?",
    }
    return [
        {"move": key, "review_question": probes[key], "genre_expectation": plan["moves"][key]}
        for key in ("thesis", "evidence", "consequence", "tradeoff", "closing")
    ]


def writing_voice_guidance(brief):
    """Compact instruction used in an existing generation call; zero extra calls."""
    plan = editorial_voice_plan(brief)
    arguments = editorial_argument_plan(brief)["moves"]
    return (
        "\nLENTE EDITORIAL ADAPTATIVA (MDA AUTO; NÃO é persona fictícia nem outro autor): "
        + plan["lens_name"] + ". "
        + "Abertura: " + plan["opening"] + " "
        + "INTRODUÇÃO JORNALÍSTICA OBRIGATÓRIA: abra com um gancho verdadeiro, "
        + "específico e interessante; explique o tema em linguagem clara, por que "
        + "importa agora e o que o leitor entenderá ou poderá decidir. "
        + "Evite suspense vazio, clickbait, fórmulas genéricas e afirmações sem fonte. "
        + "A abertura deve fluir naturalmente para o desenvolvimento e adaptar-se "
        + "ao gênero, sem exigir tamanho fixo ou subtítulos artificiais. "
        + "Progressão: " + plan["development"] + " "
        + "Desfecho: " + plan["ending"] + " "
        + "Cada parte deve acrescentar evidência, distinção, consequência ou orientação. "
        + "Não faça uma seção por movimento obrigatório, não fabrique contraste "
        + "nem varie frases artificialmente. Preserve limites, exceções e "
        + "a correspondência entre afirmação e fonte; quando faltar prova, marque pendência. "
        + "Antes de recomendar uma ação, confira se ela resolve o sintoma sem desativar ""justamente a função que o leitor quer preservar. ""Não introduza preços, capacidades, percentuais ou causalidades sem lastro explícito. ""Corte paráfrases e fechamentos decorativos sem cortar raciocínio. "
        + "MOVIMENTO ARGUMENTATIVO (organize pelo mérito, sem copiar estruturas externas): "
        + "Tese: " + arguments["thesis"] + " "
        + "Prova: " + arguments["evidence"] + " "
        + "Consequência: " + arguments["consequence"] + " "
        + "Contrapeso: " + arguments["tradeoff"] + " "
        + "Veredito/limite: " + arguments["closing"] + " "
        + "Transforme dados em critérios úteis, sem reproduzir fórmulas de outro veículo. "
        + "Não atribua à redação testes, fotografias, benchmarks ou uso de aparelhos "
        + "não executados e documentados; atribua medições de terceiros. "
        + "Preço e disponibilidade somente com fonte, data, mercado e variante. "
        + "Nunca deixe marcadores editoriais como [jogo X], [inserir fonte], "
        + "TODO ou metacomentários sobre o briefing no artigo entregue: "
        + "identifique o caso real em fonte confiável ou retire o exemplo. "
        + "Em temas regulatórios, homologação de equipamento não comprova "
        + "autorização de operação da empresa, disponibilidade comercial, "
        + "cobertura, preço ou contrato. Distinga os atos e seus documentos. "
        + "Não invente conclusão forte quando a pauta não a sustenta. "
        + "O DNA ConexoTech e a revisão humana por versão continuam prevalecendo.\n"
    )


def editorial_placeholder_signals(markdown):
    """Block only high-confidence production artifacts; never verify facts.

    Keep Markdown citations/links and instructional samples intact. A missing
    source must be reported in prose, never filled with "[jogo X]" or TODO.
    """
    if not isinstance(markdown, str):
        raise ValueError("texto inválido para auditoria de integridade")
    lines = []
    fenced = False
    marker = None
    for line in markdown.splitlines():
        fence = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence:
            glyph = fence.group(1)[0]
            if not fenced:
                fenced, marker = True, glyph
            elif glyph == marker:
                fenced, marker = False, None
            continue
        if not fenced:
            lines.append(line)
    body = "\n".join(lines)
    # [Apple](https://...) is a citation/link, not an unfinished manuscript.
    body = re.sub(r"\[[^]\n]+\]\(https?://[^)\n]+\)", "", body)
    placeholder = re.compile(
        r"\[(?:\s*(?:jogo|produto|modelo|marca|nome|empresa|autor|cidade|"
        r"pre[cç]o|dado|n[uú]mero|fonte|link|imagem|data)\s+"
        r"(?:x|y|z|a\s+definir|a\s+confirmar)\s*|"
        r"(?:inserir|preencher|adicionar|substituir|todo|tbd|xxx)"
        r"[^]\n]{0,80}|link\s+afiliado)\]",
        re.IGNORECASE,
    )
    meta = re.compile(
        r"\b(?:este\s+texto\s+segue\s+o\s+briefing\s+editorial|"
        r"como\s+modelo\s+de\s+linguagem|"
        r"este\s+artigo\s+foi\s+(?:gerado|produzido)\s+(?:por|com)\s+(?:um\s+)?prompt)\b",
        re.IGNORECASE,
    )
    signals = []
    if placeholder.search(body):
        signals.append("marcador_editorial_nao_resolvido")
    if meta.search(body):
        signals.append("metatexto_de_producao_no_artigo")
    return {
        "scope": "artefatos_formais_alta_confianca_nao_checagem_factual",
        "signals": signals,
        "factual_approval": False,
        "publication_authorized": False,
    }


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



def markdown_table_structure_signals(markdown):
    """Conservative checks for malformed standard Markdown tables.

    This is a formatting preflight, NOT semantic/factual approval. Detects
    uneven cell counts (a defect found in the 4-genre MDA A/B pilot).
    Ignore code fences and non-table prose with pipes to reduce false alerts.
    """
    if not isinstance(markdown, str):
        raise ValueError("texto inválido para auditoria de tabelas")

    def cells(row):
        line = row.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        return [part.strip() for part in re.split(r"(?<!\\)\|", line)]

    def separator(row):
        values = cells(row)
        return len(values) >= 2 and all(
            re.fullmatch(r":?-{3,}:?", item) for item in values
        )

    blocks = []
    current = []
    fenced = False
    fence_mark = None
    for line in markdown.splitlines() + [""]:
        stripped = line.lstrip()
        boundary = re.match(r"^(\x60{3,}|~{3,})", stripped)
        if boundary:
            marker = boundary.group(1)[0]
            if not fenced:
                fenced = True
                fence_mark = marker
            elif marker == fence_mark:
                fenced = False
                fence_mark = None
            if current:
                blocks.append(current)
                current = []
            continue
        if not fenced and stripped.startswith("|") and stripped.count("|") >= 2:
            current.append(stripped)
        elif current:
            blocks.append(current)
            current = []
    signals = []
    inspected = 0
    for rows in blocks:
        if len(rows) < 2:
            continue
        if not separator(rows[1]):
            # Require 3 rows before assuming the block is a table at all.
            if len(rows) >= 3 and "tabela_markdown_sem_separador" not in signals:
                signals.append("tabela_markdown_sem_separador")
            continue
        inspected += 1
        widths = [len(cells(row)) for row in rows]
        if len(set(widths)) > 1 and "tabela_markdown_colunas_inconsistentes" not in signals:
            signals.append("tabela_markdown_colunas_inconsistentes")
    return {
        "scope": "estrutura_markdown_nao_aprovacao_editorial",
        "tables_inspected": inspected,
        "signals": signals,
        "factual_approval": False,
        "publication_authorized": False,
    }


# Advisory receipt consolidation only. The operational WordPress Gate is the
# sole authority for authentication, version approval and publication.
EDITORIAL_REQUIRED_RECEIPTS = (
    "full_article", "introduction_review", "factual_review",
    "source_review", "image_license", "independent_human_review",
    "responsive_390", "responsive_1440", "wordpress_gate_test",
)


def editorial_readiness(markdown, receipts):
    """Fail closed on missing/stale evidence, without authorizing publication.

    Each receipt is bound to the exact content SHA and requires a recorded
    reviewer, evidence reference and date. Authenticity is NOT verified here;
    the operational Gate must validate trusted provenance separately.
    """
    import hashlib
    if not isinstance(markdown, str) or not markdown.strip():
        raise ValueError("artigo completo obrigatório")
    if not isinstance(receipts, dict):
        raise ValueError("comprovantes devem ser um objeto")
    sha = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    missing = []
    for name in EDITORIAL_REQUIRED_RECEIPTS:
        item = receipts.get(name)
        if not isinstance(item, dict) or (
            item.get("status") != "approved"
            or item.get("content_sha256") != sha
            or any(
                not isinstance(item.get(field), str) or not item[field].strip()
                for field in ("reviewer", "evidence", "date")
            )
        ):
            missing.append(name)
    return {
        "schema": "conexo-editorial-readiness/1",
        "content_sha256": sha,
        "ready_for_gate": not missing,
        "missing_receipts": missing,
        "publication_authorized": False,
        "note": "Apenas diagnóstico: Gate operacional deve autenticar pareceres.",
    }
