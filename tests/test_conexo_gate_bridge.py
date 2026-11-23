from __future__ import annotations

import hashlib

import pytest

from mkt_flow_p0.conexo_gate_bridge import (
    GATE_BRIEF_SCHEMA,
    GATE_POLICY_VERSION,
    build_gate_assessment_request,
    build_gate_quality_record_request,
    gate_snapshot_digest,
    gate_snapshot_fingerprint,
)
from mkt_flow_p0.revisor_qualidade_unico import (
    GATE_REQUIRED_CHECKS,
    avaliar_artigo_gate_v3,
    fingerprint_artigo,
)

POST_ID = 9768
AUTHOR_ID = 41
FEATURED_MEDIA_ID = 9714
SNAPSHOT_ID = "a1f55c35-8e56-4e1a-8d5e-2d2d5f3b1e11"
REVIEWER = "editor-independente-42"
PERSONA = (
    "Pessoa leitora que administra tecnologia no cotidiano, compara soluções "
    "e precisa entender limites sem depender de jargão técnico."
)
BRIEF = {
    "genre": "guia",
    "reader": "Leitores que precisam compreender escolhas técnicas e consequências práticas.",
    "need": "Precisam comparar alternativas sem confundir especificações e promessas.",
    "angle": "Explicar critérios de decisão em cenários concretos de utilização.",
    "contribution": "Conectar documentação, limites observados e consequências úteis.",
    "limits": "Não atribuir testes próprios nem resultados sem evidência verificável.",
}
TITLE = "Como avaliar uma solução técnica antes de alterar sua configuração"
SLUG = "como-avaliar-solucao-tecnica-antes-alterar-configuracao"
EXCERPT = (
    "Entenda os critérios de escolha, as consequências de cada ajuste e os limites "
    "da documentação antes de mudar a configuração do equipamento."
)
PARAGRAPH = (
    "A documentação descreve possibilidades e limites que precisam ser comparados "
    "com o cenário concreto de utilização. Uma decisão segura considera a versão "
    "instalada, o contexto de uso, os efeitos esperados e a possibilidade de retornar "
    "à configuração anterior quando a mudança não resolver a necessidade."
)
CONTENT = (
    "<p>" + (PARAGRAPH + " ") * 38 + "</p>"
    + '<p>Consulte a <a href="https://source.example.org/primary">documentação primária</a>.</p>'
    + '<p>Veja também o <a href="https://conexotech.com.br/guia-relacionado">guia relacionado</a>.</p>'
    + '<img src="https://conexotech.com.br/wp-content/uploads/ilustracao.webp" '
      'alt="Ilustração contextual da configuração analisada" />'
)
CONTENT_TEXT = (PARAGRAPH + " ") * 38


def wordpress_post():
    return {
        "id": POST_ID,
        "status": "draft",
        "type": "post",
        "slug": SLUG,
        "title": {"raw": TITLE, "rendered": TITLE},
        "content": {"raw": CONTENT, "rendered": CONTENT},
        "excerpt": {"raw": EXCERPT, "rendered": EXCERPT},
        "author": AUTHOR_ID,
        "date_gmt": "2026-11-23T10:00:00",
        "categories": [12],
        "tags": [13],
        "featured_media": FEATURED_MEDIA_ID,
    }


def gate_snapshot():
    snapshot = {
        "post_id": POST_ID,
        "post_type": "post",
        "post_status": "draft",
        "slug": SLUG,
        "title": TITLE,
        "content": CONTENT,
        "excerpt": EXCERPT,
        "author_id": AUTHOR_ID,
        "date_gmt": "2026-11-23 10:00:00",
        "categories": [12],
        "tags": [13],
        "featured_media": FEATURED_MEDIA_ID,
        "snapshot_id": SNAPSHOT_ID,
        "snapshot_digest_version": "cxeg-snapshot-digest-v2",
        "fingerprint_version": "cxeg-editorial-fingerprint-v2",
    }
    snapshot["fingerprint_sha256"] = gate_snapshot_fingerprint(snapshot)
    snapshot["snapshot_sha256"] = gate_snapshot_digest(snapshot)
    return snapshot


def reviewer_evidence(post):
    fp = fingerprint_artigo(post)
    evidence = {}
    for key in (
        "capa", "licenca_imagem", "alegacoes", "links_internos",
        "revisao_substantiva", "visual_390", "visual_1440",
        "voz_editorial", "persona", "imagens_internas",
    ):
        evidence[key] = {
            "fingerprint": fp,
            "reviewer": REVIEWER,
            "method": "human",
            "aprovado": True,
            "referencias": ["https://evidence.example.org/" + key],
        }
    return evidence


def reviewer_report():
    post = wordpress_post()
    return avaliar_artigo_gate_v3(
        post,
        brief=BRIEF,
        persona_profile=PERSONA,
        media={
            "id": FEATURED_MEDIA_ID,
            "alt_text": "Ilustração contextual da configuração analisada",
            "description": "Fonte individual. Licença: https://source.example.org/license",
        },
        fontes=[{
            "url": "https://source.example.org/primary",
            "verificada": True,
            "alegacoes": ["A documentação descreve os limites da configuração."],
        }],
        evidencias=reviewer_evidence(post),
        corpo_original_fonte=CONTENT_TEXT,
    )


def evidence_item(name):
    observed = "2026-11-23T13:00:00Z"
    description = "Evidência humana confrontada com a versão exata do artigo."
    if name == "capa":
        return {
            "tipo": "attachment",
            "referencia": f"wp-attachment:{FEATURED_MEDIA_ID}",
            "descricao": description,
            "observado_em": observed,
            "attachment_id": FEATURED_MEDIA_ID,
            "sha256": hashlib.sha256(b"cover-image-bytes").hexdigest(),
        }
    if name == "visual_390":
        return {
            "tipo": "screenshot",
            "referencia": "wp-attachment:390",
            "descricao": description,
            "observado_em": observed,
            "attachment_id": 390,
            "sha256": hashlib.sha256(b"screenshot-390-bytes").hexdigest(),
        }
    if name == "visual_1440":
        return {
            "tipo": "screenshot",
            "referencia": "wp-attachment:1440",
            "descricao": description,
            "observado_em": observed,
            "attachment_id": 1440,
            "sha256": hashlib.sha256(b"screenshot-1440-bytes").hexdigest(),
        }
    if name == "imagens_internas":
        return {
            "tipo": "snapshot",
            "referencia": f"snapshot:{SNAPSHOT_ID}#inline-images",
            "descricao": description,
            "observado_em": observed,
        }
    if name in {"licenca_imagem", "fontes", "alegacoes", "links_internos", "seo"}:
        return {
            "tipo": "url",
            "referencia": "https://evidence.example.org/gate/" + name,
            "descricao": description,
            "observado_em": observed,
        }
    return {
        "tipo": "snapshot",
        "referencia": f"snapshot:{SNAPSHOT_ID}#{name}",
        "descricao": description,
        "observado_em": observed,
    }


def gate_evidence(report=None):
    report = report or reviewer_report()
    result = {}
    for key in GATE_REQUIRED_CHECKS:
        items = [evidence_item(key)]
        for ref in report["checks"][key].get("evidencia", []):
            if isinstance(ref, str) and ref.startswith(("https://", "http://")):
                if not any(item["referencia"] == ref for item in items):
                    items.append({
                        "tipo": "url",
                        "referencia": ref,
                        "descricao": "Referência citada pelo Revisor Único para esta versão.",
                        "observado_em": "2026-11-23T13:00:00Z",
                    })
        result[key] = {
            "estado": "VERIFICADO",
            "reviewer": REVIEWER,
            "fingerprint": report["fingerprint"],
            "evidencia": items,
        }
    return result


def build_request(**overrides):
    report = overrides.pop("reviewer_report", None) or reviewer_report()
    args = {
        "wordpress_post": wordpress_post(),
        "gate_snapshot": gate_snapshot(),
        "reviewer_report": report,
        "mkt_brief": BRIEF,
        "persona_profile": PERSONA,
        "gate_human_evidence": gate_evidence(report),
        "reviewer_key_id": "reviewer-key-42",
    }
    args.update(overrides)
    return build_gate_quality_record_request(**args)


def test_mkt_reviewer_v2_has_all_gate_dimensions_and_never_authorizes():
    report = reviewer_report()
    assert report["schema"] == "conexo-article-quality/2"
    assert tuple(report["checks"]) == GATE_REQUIRED_CHECKS
    assert report["veredito"] == "APTO_PARA_APROVACAO"
    assert report["reviewer"] == REVIEWER
    assert report["publication_authorized"] is False
    assert report["publicacao_autorizada"] is False


def test_gate_quality_request_binds_snapshot_brief_and_sixteen_human_checks():
    request = build_request()
    assert request["contract"] == "conexo-quality-record/3"
    assert request["policy_version"] == GATE_POLICY_VERSION
    assert request["brief_schema"] == GATE_BRIEF_SCHEMA
    assert set(request["brief"]) == {
        "genre", "persona", "reader", "need", "angle", "contribution", "limits"
    }
    assert request["brief"]["persona"] == PERSONA
    assert tuple(request["checks"]) == GATE_REQUIRED_CHECKS
    assert all(item["origem"] == "humana" for item in request["checks"].values())
    assert request["publication_authorized"] is False
    assert request["factual_approval"] is False


def test_gate_preflight_request_uses_same_explicit_persona_contract():
    request = build_gate_assessment_request(
        gate_snapshot=gate_snapshot(),
        mkt_brief=BRIEF,
        persona_profile=PERSONA,
    )
    assert request["post_id"] == POST_ID
    assert request["snapshot_id"] == SNAPSHOT_ID
    assert request["brief"]["persona"] == PERSONA
    assert request["publication_authorized"] is False


def test_missing_explicit_persona_fails_closed():
    with pytest.raises(ValueError, match="explicit_persona_profile_required"):
        build_gate_assessment_request(
            gate_snapshot=gate_snapshot(),
            mkt_brief=BRIEF,
            persona_profile="",
        )


def test_flattened_or_rendered_content_is_not_accepted_as_native_raw_readback():
    post = wordpress_post()
    post["content"] = CONTENT
    with pytest.raises(ValueError, match="wordpress_native_raw_readback_required_content"):
        build_request(wordpress_post=post)


def test_gate_snapshot_digest_tampering_is_rejected():
    snapshot = gate_snapshot()
    snapshot["content"] += "<p>Changed after capture.</p>"
    with pytest.raises(ValueError, match="gate_snapshot_digest_mismatch|gate_snapshot_fingerprint_mismatch"):
        build_request(gate_snapshot=snapshot)


def test_snapshot_from_another_post_is_rejected():
    snapshot = gate_snapshot()
    snapshot["post_id"] += 1
    snapshot["fingerprint_sha256"] = gate_snapshot_fingerprint(snapshot)
    snapshot["snapshot_sha256"] = gate_snapshot_digest(snapshot)
    with pytest.raises(ValueError, match="wordpress_readback_mismatch_post_id"):
        build_request(gate_snapshot=snapshot)


def test_mkt_reviewer_fingerprint_mismatch_is_rejected():
    report = reviewer_report()
    report["fingerprint"] = "a" * 64
    with pytest.raises(ValueError, match="reviewer_report_fingerprint_mismatch"):
        build_request(reviewer_report=report)


def test_review_report_with_pending_human_check_is_rejected():
    report = reviewer_report()
    report["checks"]["persona"]["estado"] = "NAO_VERIFICADO"
    report["veredito"] = "REVISAO_NECESSARIA"
    with pytest.raises(ValueError, match="reviewer_check_not_verified_persona"):
        build_request(reviewer_report=report)


def test_reviewer_report_persona_must_match_gate_brief_persona():
    report = reviewer_report()
    report["persona_sha256"] = "a" * 64
    with pytest.raises(ValueError, match="reviewer_report_persona_hash_mismatch"):
        build_request(reviewer_report=report)


def test_reviewer_report_mkt_brief_must_match_the_current_mkt_brief():
    report = reviewer_report()
    report["brief_sha256"] = "a" * 64
    with pytest.raises(ValueError, match="reviewer_report_brief_hash_mismatch"):
        build_request(reviewer_report=report)


def test_reviewer_report_lens_must_match_canonical_brief_genre():
    report = reviewer_report()
    report["voice_lens"] = "factual"
    with pytest.raises(ValueError, match="reviewer_report_voice_lens_mismatch"):
        build_request(reviewer_report=report)


def test_gate_contract_requires_all_sixteen_human_evidence_groups():
    report = reviewer_report()
    evidence = gate_evidence(report)
    del evidence["voz_editorial"]
    with pytest.raises(ValueError, match="all_16_gate_human_evidence_groups_required"):
        build_request(gate_human_evidence=evidence, reviewer_report=report)


def test_human_evidence_must_bind_both_review_fingerprint_and_reviewer():
    report = reviewer_report()
    evidence = gate_evidence(report)
    evidence["persona"]["fingerprint"] = "b" * 64
    with pytest.raises(ValueError, match="gate_human_evidence_mkt_fingerprint_mismatch_persona"):
        build_request(gate_human_evidence=evidence, reviewer_report=report)


def test_visual_evidence_requires_real_screenshot_type():
    report = reviewer_report()
    evidence = gate_evidence(report)
    evidence["visual_390"]["evidencia"] = [{
        "tipo": "url",
        "referencia": "https://evidence.example.org/visual-390",
        "descricao": "Uma URL não substitui a captura visual.",
        "observado_em": "2026-11-23T13:00:00Z",
    }]
    with pytest.raises(ValueError, match="gate_visual_screenshot_required_visual_390"):
        build_request(gate_human_evidence=evidence, reviewer_report=report)


def test_cover_requires_exact_featured_media_attachment():
    report = reviewer_report()
    evidence = gate_evidence(report)
    wrong = evidence_item("capa")
    wrong["attachment_id"] = 999
    wrong["referencia"] = "wp-attachment:999"
    evidence["capa"]["evidencia"] = [wrong]
    with pytest.raises(ValueError, match="gate_cover_attachment_must_match_featured_media"):
        build_request(gate_human_evidence=evidence, reviewer_report=report)


def test_snapshot_evidence_must_reference_current_gate_snapshot():
    report = reviewer_report()
    evidence = gate_evidence(report)
    evidence["persona"]["evidencia"][0]["referencia"] = (
        "snapshot:11111111-1111-4111-8111-111111111111#persona"
    )
    with pytest.raises(ValueError, match="gate_snapshot_evidence_must_bind_exact_snapshot_persona"):
        build_request(gate_human_evidence=evidence, reviewer_report=report)


def test_brief_cannot_be_smuggled_with_extra_fields():
    brief = dict(BRIEF, approval=True)
    with pytest.raises(ValueError, match="mkt_brief_must_match_canonical_six_field_schema"):
        build_request(mkt_brief=brief)


def test_gate_evidence_timestamp_must_be_valid_utc():
    report = reviewer_report()
    evidence = gate_evidence(report)
    evidence["fontes"]["evidencia"][0]["observado_em"] = "2026-02-30T10:00:00Z"
    with pytest.raises(ValueError, match="gate_human_evidence_timestamp_invalid_fontes"):
        build_request(gate_human_evidence=evidence, reviewer_report=report)


def test_persona_evidence_must_be_human_not_assisted():
    post = wordpress_post()
    evidence = reviewer_evidence(post)
    evidence["persona"]["method"] = "assisted"
    report = avaliar_artigo_gate_v3(
        post,
        brief=BRIEF,
        persona_profile=PERSONA,
        media={
            "id": FEATURED_MEDIA_ID,
            "alt_text": "Ilustração contextual da configuração analisada",
            "description": "Fonte individual. Licença: https://source.example.org/license",
        },
        fontes=[{
            "url": "https://source.example.org/primary",
            "verificada": True,
            "alegacoes": ["A documentação descreve os limites da configuração."],
        }],
        evidencias=evidence,
        corpo_original_fonte=CONTENT_TEXT,
    )
    assert report["checks"]["persona"]["estado"] == "NAO_VERIFICADO"
    assert report["veredito"] == "REVISAO_NECESSARIA"
    assert report["publication_authorized"] is False


def test_missing_persona_does_not_pass_reviewer_v2():
    post = wordpress_post()
    report = avaliar_artigo_gate_v3(
        post,
        brief=BRIEF,
        persona_profile=None,
        media={
            "id": FEATURED_MEDIA_ID,
            "alt_text": "Ilustração contextual da configuração analisada",
            "description": "Fonte individual. Licença: https://source.example.org/license",
        },
        fontes=[{
            "url": "https://source.example.org/primary",
            "verificada": True,
            "alegacoes": ["A documentação descreve os limites da configuração."],
        }],
        evidencias=reviewer_evidence(post),
        corpo_original_fonte=CONTENT_TEXT,
    )
    assert report["checks"]["persona"]["estado"] == "NAO_VERIFICADO"
    assert report["veredito"] == "REVISAO_NECESSARIA"


def test_missing_alt_in_inline_image_blocks_reviewer_v2():
    post = wordpress_post()
    post["content"]["raw"] = post["content"]["raw"].replace(
        'alt="Ilustração contextual da configuração analisada"', ""
    )
    post["content"]["rendered"] = post["content"]["rendered"].replace(
        'alt="Ilustração contextual da configuração analisada"', ""
    )
    report = avaliar_artigo_gate_v3(
        post,
        brief=BRIEF,
        persona_profile=PERSONA,
        media={
            "id": FEATURED_MEDIA_ID,
            "alt_text": "Ilustração contextual da configuração analisada",
            "description": "Fonte individual. Licença: https://source.example.org/license",
        },
        fontes=[{
            "url": "https://source.example.org/primary",
            "verificada": True,
            "alegacoes": ["A documentação descreve os limites da configuração."],
        }],
        evidencias=reviewer_evidence(post),
        corpo_original_fonte=CONTENT_TEXT,
    )
    assert report["checks"]["imagens_internas"]["estado"] == "REPROVADO"
    assert "imagens_internas" in report["bloqueios"]
    assert report["publication_authorized"] is False


def test_gate_evidence_must_cover_every_reviewer_reference():
    report = reviewer_report()
    evidence = gate_evidence(report)
    evidence["fontes"]["evidencia"] = [
        item for item in evidence["fontes"]["evidencia"]
        if item["referencia"] != "https://source.example.org/primary"
    ]
    with pytest.raises(ValueError, match="gate_evidence_does_not_cover_reviewer_reference_fontes"):
        build_request(gate_human_evidence=evidence, reviewer_report=report)
