"""No-cost controlled A/B: same inputs and hashes, one MDA-only prompt delta."""
import hashlib
import json
from pathlib import Path

import pytest

from mkt_flow_p0.editorial_substance import writing_instruction, brief_hash
from mkt_flow_p0.editorial_voice_adapter import writing_voice_guidance
from mkt_flow_p0.rewriter import montar_prompt
from scripts.prepare_mda_ab import build_pair, prepare_case
from scripts.seal_mda_ab_review import seal_pair


BRIEF = {
    "genre": "guia",
    "reader": "Leitor brasileiro que precisa orientar uma configuração de celular.",
    "need": "Escolher o ajuste correto conforme o comportamento observado no aparelho.",
    "angle": "Separar substituição automática de sugestões e orientar mudança reversível.",
    "contribution": "Oferecer consequências práticas, fontes e limite de cada alternativa.",
    "limits": "Nenhuma experiência ou teste próprios; a versão e o idioma podem alterar menus.",
}


def case():
    return {
        "schema": "conexo-mda-ab-source/1",
        "case_id": "guia-9798",
        "title": "Ajustes do teclado",
        "source_name": "Documentação oficial e rascunho em revisão",
        "source_text": (
            "A documentação explica o controle de correção automática e as sugestões. "
            "Há diferença entre substituir uma palavra incorretamente e ver sugestões "
            "na tela. O leitor pode querer preservar a correção enquanto desativa "
            "outra função, desde que a versão do sistema permita o controle. " * 6
        ),
        "editorial_brief": BRIEF,
        "research_context": None,
        "intended_generation": {
            "model": "llama-3.3-70b-versatile", "temperature": 0.2, "max_tokens": 2400
        },
    }


def test_only_delta_is_voice_guidance_and_default_remains_mda(monkeypatch):
    import mkt_flow_p0.rewriter as rewriter
    monkeypatch.setattr(rewriter, "_get_client", lambda: (_ for _ in ()).throw(
        AssertionError("No real model invocation allowed")))
    control, mda, receipt = build_pair(case())
    assert mda.replace(writing_voice_guidance(BRIEF), "") == control
    assert receipt["only_delta"] == "mda_voice_guidance"
    assert receipt["brief_sha256"] == brief_hash(BRIEF)
    assert receipt["intended_generation"]["max_tokens"] == 2400
    assert receipt["provider_called"] is False
    assert receipt["generated_articles_present"] is False
    assert receipt["external_blind_review_completed"] is False
    assert receipt["publication_authorized"] is False
    assert receipt["factual_approval"] is False
    assert receipt["source_sha256"] == hashlib.sha256(
        case()["source_text"].encode("utf-8")).hexdigest()
    default = montar_prompt(
        case()["title"], case()["source_text"],
        fonte_nome=case()["source_name"], editorial_brief=BRIEF)
    assert default == mda


def test_pre_mda_control_is_legacy_writing_instruction_unmodified():
    old = writing_instruction(BRIEF, voice_variant="control")
    new = writing_instruction(BRIEF, voice_variant="mda")
    assert new == old + writing_voice_guidance(BRIEF)
    assert "LENTE EDITORIAL ADAPTATIVA" not in old
    assert "BRIEFING EDITORIAL" in old
    for bad in ("none", None, "", "user injection"):
        with pytest.raises(ValueError):
            writing_instruction(BRIEF, voice_variant=bad)
        with pytest.raises(ValueError):
            montar_prompt("Título", "Matéria " * 50,
                          editorial_brief=BRIEF, voice_variant=bad)


def test_private_preflight_has_no_approval_and_does_not_reuse_directory(tmp_path):
    out = tmp_path / "pilot"
    result = prepare_case(case(), out)
    assert result["quality_improvement_demonstrated"] is False
    assert result["publication_authorized"] is False
    assert (out / "control.prompt.txt").exists()
    assert (out / "mda.prompt.txt").exists()
    assert "LENTE EDITORIAL ADAPTATIVA" in (out / "mda.prompt.txt").read_text()
    assert "LENTE EDITORIAL ADAPTATIVA" not in (out / "control.prompt.txt").read_text()
    for path in out.iterdir():
        assert path.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        prepare_case(case(), out)


def test_reject_invalid_input_or_mismatched_source():
    for key, value in [
        ("case_id", "../escape"),
        ("schema", "wrong"),
        ("source_text", "short"),
        ("research_context", []),
        ("intended_generation", {"model": "llama", "temperature": 2, "max_tokens": 1000}),
    ]:
        sample = case()
        sample[key] = value
        with pytest.raises(ValueError):
            build_pair(sample)


def test_blind_pair_separate_key_and_no_false_human_approval(tmp_path):
    control, treatment, manifest = build_pair(case())
    control_article = ("Texto de controle com referência real e limites claramente "
                       "descritos para orientar o leitor sem extrapolar fontes. ") * 7
    mda_article = ("Texto experimental MDA que distingue cenários e expõe o limite "
                   "de cada decisão, sem fabricar dados ou experiências. ") * 7
    first, second = tmp_path / "blind", tmp_path / "key"
    result = seal_pair(manifest, control_article, mda_article, first, second, coin=1)
    blind = (first / "review_A_B.md").read_text()
    key = json.loads((second / "mapping.private.json").read_text())
    assert result["human_review_completed"] is False
    assert "======== TEXTO A ========" in blind
    assert "======== TEXTO B ========" in blind
    assert "Texto experimental MDA" in blind.split("TEXTO A ========")[1]
    assert "Texto de controle" in blind.split("TEXTO B ========")[1]
    assert "control_prompt_sha256" not in blind
    assert "mda_voice_guidance" not in blind
    assert key["mapping"] == {"A": "mda", "B": "control"}
    assert key["quality_improvement_demonstrated"] is False
    assert key["publication_authorized"] is False
    assert (first / "review_A_B.md").stat().st_mode & 0o077 == 0
    assert (second / "mapping.private.json").stat().st_mode & 0o077 == 0
    with pytest.raises(ValueError):
        seal_pair(manifest, control_article, mda_article,
                  tmp_path / "nested", tmp_path / "nested" / "key", coin=0)
    with pytest.raises(ValueError):
        seal_pair(manifest, control_article, control_article,
                  tmp_path / "x", tmp_path / "y", coin=0)


def test_generation_model_is_not_claimed_verified_by_local_seal(tmp_path):
    _, _, manifest = build_pair(case())
    article1 = "Controle, com fatos e fontes citadas dentro dos limites documentados. " * 14
    article2 = "Tratamento, com raciocínio e contexto dentro das fontes existentes. " * 14
    result = seal_pair(manifest, article1, article2,
                       tmp_path / "blind", tmp_path / "key", coin=0)
    assert result["model_execution_verified"] is False
    assert result["publication_authorized"] is False
