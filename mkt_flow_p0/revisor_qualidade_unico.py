"""Revisor Editorial Unico: avalia snapshot WordPress sem publicar nem aprovar.

Entrada: WP MCP posts_get(context=edit) + media_get + fontes e evidencias verificadas.
Nao consulta rede, nao inventa licencas nem substitui revisor humano.
A nota de prioridade 1..10 e intencionalmente independente deste parecer.
"""
from datetime import datetime, timezone
import hashlib
import json
import re
from html import unescape
from urllib.parse import urlparse

from mkt_flow_p0.gate_editorial_pos_ia import validar_saida
from mkt_flow_p0.editorial_voice_adapter import editorial_placeholder_signals

VERSAO = "conexo-article-quality/1"
HOST = "conexotech.com.br"
VALIDOS = {"VERIFICADO", "REPROVADO", "NAO_VERIFICADO"}
REQUIRED_CHECKS = (
    "versao", "titulo", "categoria", "capa", "licenca_imagem",
    "fontes", "alegacoes", "links_internos", "seo", "html",
    "revisao_substantiva", "visual_390", "visual_1440",
)
_RE_LINK = re.compile(r'href\s*=\s*["\x27](https?://[^"\x27]+)', re.I)
_RE_TAG = re.compile(r"<[^>]+>")


def _str(value):
    if isinstance(value, dict):
        return str(value.get("raw", value.get("rendered", "")) or "")
    return str(value or "")


def _txt(raw):
    return re.sub(r"\s+", " ", unescape(_RE_TAG.sub(" ", _str(raw)))).strip()


def _post(post):
    if isinstance(post, dict) and isinstance(post.get("data"), dict):
        return post["data"]
    return post


def _sha(post):
    # Excluir status e modified: pode-se publicar sem invalidar a revisao da versao.
    # Incluir tudo que influencia o parecer, especialmente corpo, categoria e capa.
    vals = {
        "id": post.get("id"), "author": post.get("author"),
        "type": post.get("type"), "date_gmt": post.get("date_gmt"), "title": _str(post.get("title")),
        "content": _str(post.get("content")),
        "excerpt": _str(post.get("excerpt")),
        "slug": post.get("slug"), "categories": post.get("categories"),
        "featured_media": post.get("featured_media"),
    }
    raw = json.dumps(vals, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _check(state, reason="", evidence=None):
    if state not in VALIDOS:
        raise ValueError("Estado de evidencia invalido")
    return {"estado": state, "motivo": reason, "evidencia": evidence or []}


def _evidence(evidences, name, fingerprint):
    """Um parecer humano apenas vale para a versao exata, com prova consultavel."""
    e = evidences.get(name)
    if not isinstance(e, dict):
        return _check("NAO_VERIFICADO", "evidencia_ausente")
    if e.get("fingerprint") != fingerprint:
        return _check("NAO_VERIFICADO", "evidencia_de_outra_versao")
    if not isinstance(e.get("referencias"), list) or not e["referencias"]:
        return _check("NAO_VERIFICADO", "referencias_ausentes")
    if not isinstance(e.get("reviewer"), str) or not e["reviewer"].strip():
        return _check("NAO_VERIFICADO", "revisor_ausente")
    if e.get("aprovado") is not True:
        return _check("REPROVADO", "revisao_nao_aprovada", e["referencias"])
    return _check("VERIFICADO", evidence=e["referencias"])


def avaliar_artigo(post, *, media=None, fontes=None, evidencias=None,
                   titulo_original_fonte=None, corpo_original_fonte=None):
    """Analisa rascunho real, sem fazer mutacoes. Faltas de prova falham fechado.

    fontes: [{url, verificada: bool, alegacoes: [str]}].
    evidencias: revisao_substantiva, visual_390 e visual_1440,
      com fingerprint, reviewer, aprovado e referencias.
    """
    post = _post(post)
    if not isinstance(post, dict) or type(post.get("id")) is not int:
        raise ValueError("Snapshot WordPress invalido: id ausente")
    evidencias = evidencias or {}
    fontes = fontes or []
    fingerprint = _sha(post)
    checks = {}
    checks["versao"] = _check("VERIFICADO", evidence=[fingerprint])
    title = _txt(post.get("title"))
    content = _str(post.get("content"))
    excerpt = _txt(post.get("excerpt"))
    links = _RE_LINK.findall(content)
    checks["titulo"] = _check(
        "VERIFICADO" if 20 <= len(title) <= 90 and not re.search(r"(?i)\b(titulo aqui|lorem ipsum)\b", title)
        else "REPROVADO", "titulo_ausente_ou_inadequado" if not (20 <= len(title) <= 90) else "")
    cat = post.get("categories") or []
    checks["categoria"] = _check("VERIFICADO" if isinstance(cat, list) and cat and 1 not in cat
                                 else "REPROVADO", "categoria_padrao_ou_ausente" if not cat or 1 in cat else "")
    capa_id = post.get("featured_media")
    checks["capa"] = _check("VERIFICADO" if type(capa_id) is int and capa_id > 0
                           else "REPROVADO", "sem_capa" if not capa_id else "")
    med = (media.get("data", media) if isinstance(media, dict) else {}) or {}
    desc = _txt(med.get("description"))
    alt = _txt(med.get("alt_text"))
    # Metadados com link de licença sao declaracoes, nao prova de direito.
    licenca_declarada = bool(
        re.search(r"https?://\S*(?:license|licen[cs]a)", desc, re.I)
        or re.search(r"https://creativecommons\.org/publicdomain/zero/1\.0(?:[/\s?#]|$)", desc, re.I)
    )
    licenca_provada = _evidence(evidencias, "licenca_imagem", fingerprint)
    # Generated illustrations have provenance/usage evidence, not a stock license URL.
    # Metadata alone never attests rights; the human record must identify this origin.
    ia_declarada = bool(re.search(r"(?:gerad[ao]|produzid[ao]).{0,100}(?:\bIA\b|ChatGPT|intelig[eê]ncia artificial)", desc, re.I))
    origem = evidencias.get("licenca_imagem")
    origem_ia = isinstance(origem, dict) and origem.get("tipo_origem") == "gerada_ia"
    if med.get("id") != capa_id or not alt or not (licenca_declarada or ia_declarada):
        checks["licenca_imagem"] = _check("REPROVADO", "mídia_sem_alt_origem_ou_licenca_declarada")
    elif ia_declarada and not licenca_declarada and not origem_ia:
        checks["licenca_imagem"] = _check("NAO_VERIFICADO", "proveniencia_ia_sem_atestado_especifico")
    else:
        checks["licenca_imagem"] = licenca_provada
    fontes_ok = [f for f in fontes if isinstance(f, dict) and f.get("verificada") is True
                 and isinstance(f.get("url"), str) and f["url"] in links and
                 isinstance(f.get("alegacoes"), list) and f["alegacoes"]]
    checks["fontes"] = _check("VERIFICADO" if len(fontes_ok) >= 1 else "NAO_VERIFICADO",
                              "fontes_primarias_nao_evidenciadas" if not fontes_ok else "",
                              [f["url"] for f in fontes_ok])
    if corpo_original_fonte and content:
        alerta = validar_saida(_txt(corpo_original_fonte), _txt(content))
        # A numeric/style detector is not a factual verifier. Only independently
        # attested, version-bound evidence can complete this quality dimension.
        if alerta["veredito"] != "SEM_ALERTAS":
            checks["alegacoes"] = _check("REPROVADO", ",".join(alerta["motivos"]),
                                         [alerta["veredito"]])
        else:
            checks["alegacoes"] = _evidence(evidencias, "alegacoes", fingerprint)
    else:
        checks["alegacoes"] = _check("NAO_VERIFICADO", "texto_original_para_confronto_ausente")
    internos = [link for link in links if urlparse(link).hostname in (HOST, "www." + HOST)]
    # Quantidade nao basta: pertinencia precisa de revisao substantiva.
    # The DNA permits UP TO 3 genuinely related links, not a quota of 3.
    # Relevance and deliberate absence require version-bound human evidence.
    if len(set(internos)) > 3:
        checks["links_internos"] = _check("REPROVADO", "mais_de_tres_links_internos",
                                          sorted(set(internos)))
    else:
        checks["links_internos"] = _evidence(evidencias, "links_internos", fingerprint)
    slug = _str(post.get("slug"))
    checks["seo"] = _check(
        "VERIFICADO" if 20 <= len(slug) <= 100 and len(excerpt) >= 80 and
        len(content.split()) >= 250 else "NAO_VERIFICADO",
        "slug_resumo_ou_conteudo_insuficiente" if not (20 <= len(slug) <= 100 and len(excerpt) >= 80) else "")
    # Analise leve; nao faz parse DOM nem substitui verificacao visual.
    integrity = editorial_placeholder_signals(_txt(content))
    placeholders = bool(integrity["signals"]) or bool(re.search(r"\[LINK AFILIADO\]|FACHADA_VIDEO|lorem ipsum", content, re.I))
    h1 = bool(re.search(r"<h1(?:\s|>)", content, re.I))
    checks["html"] = _check("REPROVADO" if placeholders or h1 else "VERIFICADO",
                             "placeholder_ou_h1_no_corpo" if placeholders or h1 else "",
                             integrity["signals"])
    for name in ("revisao_substantiva", "visual_390", "visual_1440"):
        checks[name] = _evidence(evidencias, name, fingerprint)
    falhas = [key for key in REQUIRED_CHECKS if checks[key]["estado"] == "REPROVADO"]
    sem_prova = [key for key in REQUIRED_CHECKS if checks[key]["estado"] == "NAO_VERIFICADO"]
    veredito = ("BLOQUEADO" if falhas else
                "REVISAO_NECESSARIA" if sem_prova else
                "APTO_PARA_APROVACAO")
    return {
        "schema": VERSAO, "post_id": post["id"],
        "status_wp": post.get("status"),
        "fingerprint": fingerprint,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks, "veredito": veredito,
        "bloqueios": falhas, "pendencias": sem_prova,
        "prioridade_1a10_nao_equivale_a_qualidade": True,
        "publicacao_autorizada": False,
        "observacao": "Apto para aprovacao nao e autorizacao de publicacao; gate e revisor humano independentes.",
    }


def verificar_versao(parecer, post_atual):
    """Impedir uso de parecer obsoleto mesmo se WordPress modified nao mudar."""
    return bool(isinstance(parecer, dict) and
                parecer.get("schema") == VERSAO and
                parecer.get("post_id") == _post(post_atual).get("id") and
                parecer.get("fingerprint") == _sha(_post(post_atual)))


# Contract v2 for the independent reviewer -> Conexo Gate v3 handoff.
GATE_VERSAO = "conexo-article-quality/2"
GATE_REQUIRED_CHECKS = (
    "versao", "titulo", "categoria", "voz_editorial", "persona", "capa",
    "imagens_internas", "licenca_imagem", "fontes", "alegacoes",
    "links_internos", "seo", "html", "revisao_substantiva",
    "visual_390", "visual_1440",
)


def fingerprint_artigo(post):
    """Expose the legacy reviewer fingerprint for an explicit bridge comparison."""
    normalized = _post(post)
    if not isinstance(normalized, dict):
        raise ValueError("snapshot WordPress inválido")
    return _sha(normalized)


def _gate_human_evidence(evidences, name, fingerprint):
    """Require explicit human evidence for the Gate v3-only dimensions."""
    evidence = evidences.get(name) if isinstance(evidences, dict) else None
    if not isinstance(evidence, dict):
        return _check("NAO_VERIFICADO", "evidencia_humana_ausente")
    if evidence.get("fingerprint") != fingerprint:
        return _check("NAO_VERIFICADO", "evidencia_de_outra_versao")
    if evidence.get("method") != "human":
        return _check("NAO_VERIFICADO", "evidencia_nao_atestada_humanamente")
    reviewer = evidence.get("reviewer")
    if not isinstance(reviewer, str) or not 3 <= len(reviewer.strip()) <= 120:
        return _check("NAO_VERIFICADO", "identidade_descritiva_do_revisor_ausente")
    references = evidence.get("referencias")
    if not isinstance(references, list) or not references:
        return _check("NAO_VERIFICADO", "referencias_humanas_ausentes")
    if any(not isinstance(item, str) or len(item.strip()) < 8 for item in references):
        return _check("NAO_VERIFICADO", "referencia_humana_invalida")
    if evidence.get("aprovado") is not True:
        return _check("REPROVADO", "atesto_humano_nao_aprovado", references)
    return _check("VERIFICADO", evidence=references)


def avaliar_artigo_gate_v3(
    post,
    *,
    brief=None,
    persona_profile=None,
    media=None,
    fontes=None,
    evidencias=None,
    titulo_original_fonte=None,
    corpo_original_fonte=None,
):
    """Evaluate the MKT reviewer report under the 16-check Gate v3 contract.

    The existing six-field MKT brief is preserved. An explicit persona profile
    is a separate required input and is combined only by the bridge adapter.
    This report is diagnostic/human evidence; it never signs or authorizes.
    """
    from mkt_flow_p0.editorial_substance import normalize_brief
    from mkt_flow_p0.editorial_voice_adapter import editorial_voice_plan

    normalized_brief = None
    try:
        normalized_brief = normalize_brief(brief)
    except (TypeError, ValueError):
        pass

    if (
        not isinstance(persona_profile, str)
        or not 20 <= len(persona_profile.strip()) <= 1200
    ):
        persona_profile = None
    else:
        persona_profile = persona_profile.strip()

    evidences = evidencias if isinstance(evidencias, dict) else {}
    base = avaliar_artigo(
        post,
        media=media,
        fontes=fontes,
        evidencias=evidencias,
        titulo_original_fonte=titulo_original_fonte,
        corpo_original_fonte=corpo_original_fonte,
    )
    normalized_post = _post(post)
    fingerprint = base["fingerprint"]
    checks = dict(base["checks"])

    if normalized_brief is None:
        checks["voz_editorial"] = _check("NAO_VERIFICADO", "brief_mkt_de_seis_campos_ausente_ou_invalido")
    else:
        plan = editorial_voice_plan(normalized_brief)
        voice_check = _gate_human_evidence(evidences, "voz_editorial", fingerprint)
        if voice_check["estado"] == "VERIFICADO":
            voice_check["motivo"] = "lente_esperada:" + plan["lens"]
        checks["voz_editorial"] = voice_check

    if persona_profile is None:
        checks["persona"] = _check("NAO_VERIFICADO", "perfil_explicito_de_persona_ausente_ou_invalido")
    else:
        checks["persona"] = _gate_human_evidence(evidences, "persona", fingerprint)

    content = _str(normalized_post.get("content"))
    image_tags = re.findall(r"<img\b[^>]*>", content, re.I)
    image_errors = []
    for index, tag in enumerate(image_tags):
        src = re.search(r'\bsrc\s*=\s*["\']([^"\']+)["\']', tag, re.I)
        alt = re.search(r'\balt\s*=\s*["\']([^"\']*)["\']', tag, re.I)
        if not src or not src.group(1).strip():
            image_errors.append("imagem_sem_src_" + str(index))
        if not alt or not alt.group(1).strip():
            image_errors.append("imagem_sem_alt_" + str(index))
    if image_errors:
        checks["imagens_internas"] = _check("REPROVADO", ",".join(image_errors))
    else:
        image_check = _gate_human_evidence(evidences, "imagens_internas", fingerprint)
        if image_check["estado"] == "VERIFICADO" and not image_tags:
            image_check["motivo"] = "ausencia_de_imagem_interna_atestada_humanamente"
        checks["imagens_internas"] = image_check

    # The Gate requires a reviewer attestation for the actual featured asset,
    # not merely a non-zero featured_media field.
    cover_human = _gate_human_evidence(evidences, "capa", fingerprint)
    if checks.get("capa", {}).get("estado") == "VERIFICADO":
        checks["capa"] = cover_human
    elif checks.get("capa", {}).get("estado") != "REPROVADO":
        checks["capa"] = _check("REPROVADO", "capa_wordpress_invalida")

    required = set(GATE_REQUIRED_CHECKS)
    missing = required - set(checks)
    for key in missing:
        checks[key] = _check("NAO_VERIFICADO", "dimensao_obrigatoria_ausente")

    blocked = [key for key in GATE_REQUIRED_CHECKS if checks[key]["estado"] == "REPROVADO"]
    pending = [key for key in GATE_REQUIRED_CHECKS if checks[key]["estado"] == "NAO_VERIFICADO"]
    reviewer_names = {
        item.get("reviewer").strip()
        for item in evidences.values()
        if isinstance(item, dict)
        and item.get("fingerprint") == fingerprint
        and isinstance(item.get("reviewer"), str)
        and item.get("reviewer").strip()
    }
    reviewer = next(iter(reviewer_names)) if len(reviewer_names) == 1 else None
    if len(reviewer_names) > 1:
        pending.append("identidades_de_revisor_inconsistentes")

    report = {
        "schema": GATE_VERSAO,
        "post_id": int(normalized_post["id"]),
        "status_wp": normalized_post.get("status"),
        "fingerprint": fingerprint,
        "reviewed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "reviewer": reviewer,
        "brief_sha256": (
            __import__("mkt_flow_p0.editorial_substance", fromlist=["brief_hash"]).brief_hash(normalized_brief)
            if normalized_brief is not None else None
        ),
        "persona_sha256": hashlib.sha256(persona_profile.encode("utf-8")).hexdigest() if persona_profile else None,
        "voice_lens": (
            editorial_voice_plan(normalized_brief)["lens"] if normalized_brief is not None else None
        ),
        "checks": checks,
        "veredito": "BLOQUEADO" if blocked else ("REVISAO_NECESSARIA" if pending else "APTO_PARA_APROVACAO"),
        "bloqueios": blocked,
        "pendencias": list(dict.fromkeys(pending)),
        "factual_approval": False,
        "publicacao_autorizada": False,
        "publication_authorized": False,
        "observacao": "Parecer v2 não é Quality Record assinado, Owner Approval, Owner Release ou autorização de publicação.",
    }
    if report["pendencias"] and report["veredito"] == "APTO_PARA_APROVACAO":
        report["veredito"] = "REVISAO_NECESSARIA"
    if report["bloqueios"]:
        report["veredito"] = "BLOQUEADO"
    report["checks"] = {key: checks[key] for key in GATE_REQUIRED_CHECKS}
    return report
