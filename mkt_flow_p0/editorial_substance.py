"""Shared editorial brief and text-bound substantive review, without network.

Evidence excerpts make the review auditable; they do not certify the reviewer's
judgment or external facts. No score grants publication permission.
"""
import hashlib
import json
import re

GENRES = {"noticia", "guia", "analise", "comparativo", "review", "nota_breve"}
CRITERIA = ("reader_need", "editorial_angle", "decision_support", "voice", "source_limits")
RUBRIC = {
    "reader_need": "O início atende um problema concreto do leitor definido no briefing.",
    "editorial_angle": "Há progressão com movimentos úteis e recorte próprio, não sequência de fontes ou seções sem função.",
    "decision_support": "Interpreta evidências, distingue cenários e tensões reais, preserva limites e auxilia a decidir; sem extrapolar.",
    "voice": "A voz decorre de escolhas fundamentadas e ritmo proporcional à ideia, sem persona encenada ou fechos decorativos.",
    "source_limits": "O texto distingue documentação, inferência e experiência; explicita limites relevantes.",
}


def content_hash(markdown):
    return hashlib.sha256(markdown.encode("utf-8")).hexdigest()


def normalize_brief(value):
    fields = {"genre", "reader", "need", "angle", "contribution", "limits"}
    if not isinstance(value, dict) or set(value) != fields or value.get("genre") not in GENRES:
        raise ValueError("briefing editorial inválido")
    if any(not isinstance(value[k], str) or not 20 <= len(value[k].strip()) <= 1200
           for k in fields - {"genre"}):
        raise ValueError("briefing exige leitor, necessidade, recorte, contribuição e limites concretos")
    return {k: v.strip() for k, v in value.items()}


def brief_hash(brief):
    return content_hash(json.dumps(normalize_brief(brief), ensure_ascii=False, sort_keys=True))


def writing_instruction(brief, *, voice_variant="mda"):
    """MDA default; explicit control restores the prior prompt for offline A/B."""
    if voice_variant not in ("control", "mda"):
        raise ValueError("variante editorial inválida")
    from mkt_flow_p0.editorial_voice_adapter import writing_voice_guidance
    brief = normalize_brief(brief)
    return (
        "\nBRIEFING EDITORIAL (restrições de fatos prevalecem):\n"
        + json.dumps(brief, ensure_ascii=False)
        + "\nDesenvolva esse recorte, não faça tradução integral nem resumo sequencial das fontes. "
        "Comece pela necessidade do leitor; selecione e hierarquize os fatos. Acrescente "
        "raciocínio útil, exemplos explicitamente hipotéticos ou critérios de decisão "
        "sustentados pelos insumos. Explique por que uma opção serve e onde deixa de servir. "
        "Voz independente significa julgamento fundamentado, nunca bordões ou opinião inventada. "
        "Não invente experiência própria, contexto brasileiro, preços ou defeitos para dar personalidade. "
        "Se faltarem dados para a contribuição pedida, explicite a lacuna; não preencha com volume.\n"
        + (writing_voice_guidance(brief) if voice_variant == "mda" else "")
    )


def _near_duplicate_repetition(paragraphs):
    """Flag large amounts of lightly reworded padding, not shared short phrases."""
    fingerprints = []
    for paragraph in paragraphs:
        words = re.findall(r"\w+", paragraph.casefold())
        if len(words) < 25:
            continue
        grams = {tuple(words[i:i + 4]) for i in range(len(words) - 3)}
        fingerprints.append(grams)
    if len(fingerprints) < 4:
        return False
    unique = []
    repeated = 0
    for grams in fingerprints:
        if any(len(grams & earlier) / len(grams | earlier) >= .72 for earlier in unique):
            repeated += 1
        else:
            unique.append(grams)
    return repeated >= 2 and repeated * 3 >= len(fingerprints)


def assess_substance(markdown, brief=None, review=None):
    """Review is a supplied assessment, never proof of semantic truth or identity."""
    pending = []
    try:
        normalized = normalize_brief(brief)
    except ValueError:
        normalized = None
        pending.append("briefing_editorial_ausente_ou_invalido")
    paragraphs = [re.sub(r"\s+", " ", p).strip().casefold()
                  for p in markdown.split("\n\n") if len(p.split()) > 12]
    sentences = [s.strip().casefold() for s in re.split(r"[.!?]\s+", markdown) if len(s.split()) > 6]
    if ((len(paragraphs) > 2 and len(set(paragraphs)) / len(paragraphs) < .7)
            or (len(sentences) > 5 and len(set(sentences)) / len(sentences) < .5)
            or _near_duplicate_repetition(paragraphs)):
        pending.append("repeticao_substantiva")
    # Structural manuscript defects remain pending regardless of a favorable
    # assisted review: the reviewer is not a factual or publication gate.
    from mkt_flow_p0.editorial_voice_adapter import editorial_placeholder_signals
    pending.extend(editorial_placeholder_signals(markdown)["signals"])
    valid = isinstance(review, dict) and normalized is not None
    valid = valid and review.get("content_sha256") == content_hash(markdown)
    valid = valid and review.get("brief_sha256") == brief_hash(normalized)
    valid = valid and review.get("method") in {"assisted", "human"}
    valid = valid and isinstance(review.get("reviewer"), str) and 3 <= len(review["reviewer"]) <= 120
    checks = review.get("criteria") if isinstance(review, dict) else None
    valid = valid and isinstance(checks, dict) and set(checks) == set(CRITERIA)
    scores = {}
    if valid:
        for key in CRITERIA:
            item = checks[key]
            if (not isinstance(item, dict) or type(item.get("score")) is not int
                    or not 0 <= item["score"] <= 4
                    or not isinstance(item.get("reason"), str) or not 30 <= len(item["reason"].strip()) <= 1500
                    or not isinstance(item.get("excerpt"), str) or not 30 <= len(item["excerpt"]) <= 1500
                    or item["excerpt"] not in markdown):
                valid = False
                break
            scores[key] = item["score"]
    if not valid:
        pending.append("avaliacao_substantiva_ausente_invalida_ou_desatualizada")
    else:
        pending.extend("revisar_" + key for key, score in scores.items() if score < 3)
    return {"status": "PASS" if not pending else "PENDING", "pendencias": pending,
            "scores": scores if valid else {}, "content_sha256": content_hash(markdown),
            "review_valid": bool(valid), "assessment_scope": "supplied_judgment_with_textual_evidence",
            "factual_approval": False, "publication_authorized": False}


def assess_editorial_release(markdown, brief=None, review=None, receipts=None):
    """Combine the existing substantive assessment with version-bound receipts.

    This is a diagnostic entry point for the executor, NOT an authorization
    or a WordPress write. Missing receipts always block readiness.
    """
    from mkt_flow_p0.editorial_voice_adapter import editorial_readiness
    substance = assess_substance(markdown, brief, review)
    readiness = editorial_readiness(markdown, receipts if receipts is not None else {})
    blockers = list(substance["pendencias"])
    blockers.extend("comprovante_ausente_ou_invalido:" + name
                    for name in readiness["missing_receipts"])
    return {
        "status": "REQUIRES_AUTHENTICATED_GATE" if not blockers else "BLOCKED",
        "content_sha256": readiness["content_sha256"],
        "blockers": blockers,
        "substance": substance,
        "readiness": readiness,
        "publication_authorized": False,
        "factual_approval": False,
    }


def assess_editorial_package(package, brief=None, review=None, receipts=None):
    """Version-bound editorial diagnostics for a canonical package; never approval.

    Fail closed if the manuscript differs from the reviewed package content.
    The trusted release trace and canonical Gate are separate requirements.
    """
    if not isinstance(package, dict) or not isinstance(package.get("payload"), dict):
        raise ValueError("pacote editorial inválido")
    manuscript = package["payload"].get("content")
    if not isinstance(manuscript, str) or not manuscript.strip():
        raise ValueError("conteúdo editorial ausente")
    result = assess_editorial_release(manuscript, brief, review, receipts)
    result["package_version_sha256"] = package.get("version_sha256")
    result["status"] = "BLOCKED" if result["blockers"] else "REQUIRES_AUTHENTICATED_GATE"
    result["publication_authorized"] = False
    return result
