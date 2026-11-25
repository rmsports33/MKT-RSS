"""Testes offline dos construtores de prova de voz e da invalidação por edição."""
import copy
import hashlib

import pytest

from mkt_flow_p0.editorial_identity import (
    DNA_PROMPT_SHA256,
    atualizar_handoff_revisao,
    construir_prova_voz_assistida,
    construir_prova_voz_externa,
    construir_prova_voz_humana,
    criar_handoff_chatgpt,
    normalizar_aplicacao_voz,
    validar_handoff_chatgpt,
    verificar_aplicacao_voz,
)

URL = "https://example.org/font-original"
MARKDOWN = "## Título\n\nTexto estável para esta versão do artigo, com fonte atribuída.\n"
EDITADO = MARKDOWN + "\n## Edição posterior\n\nTrecho acrescentado depois da prova original.\n"
PROMPT_SHA = hashlib.sha256(b"system prompt externo de teste").hexdigest()


def artigo():
    return {"titulo_seo": "Título de teste para prova de voz", "slug": "prova-de-voz",
            "meta_description": "Descrição curta o suficiente para o teste offline.",
            "texto_markdown": MARKDOWN}


def handoff_prova(proof):
    return criar_handoff_chatgpt(
        artigo(), url_fonte=URL, voice_application=proof,
        editorial_review={"fixture": "avaliacao anterior"},
    )


@pytest.mark.parametrize("proof,status", [
    (construir_prova_voz_assistida(MARKDOWN, "codex"), "ASSISTED_ADAPTED"),
    (construir_prova_voz_humana(MARKDOWN, "Reinaldo Mendes"), "HUMAN_ADAPTED"),
    (construir_prova_voz_externa(PROMPT_SHA, "groq"), "PROMPT_APPLIED"),
])
def test_construtores_geram_provas_aceitas_pelo_validador(proof, status):
    assert proof["status"] == status
    assert proof["dna_prompt_sha256"] == DNA_PROMPT_SHA256
    assert normalizar_aplicacao_voz(proof) == proof
    assert verificar_aplicacao_voz({"editorial_voice_application": proof})["status"] == status
    handoff = handoff_prova(proof)
    assert validar_handoff_chatgpt(handoff)["valid"] is True


def test_construtores_ligam_prova_ao_texto_exato():
    assistida = construir_prova_voz_assistida(MARKDOWN, "codex")
    humana = construir_prova_voz_humana(MARKDOWN, "Reinaldo Mendes")
    esperado = hashlib.sha256(MARKDOWN.encode("utf-8")).hexdigest()
    assert assistida["content_sha256"] == esperado
    assert humana["content_sha256"] == esperado
    assert assistida["method"] == "assisted_editorial_adaptation"
    assert humana["method"] == "human_editorial_check"
    assert construir_prova_voz_externa(PROMPT_SHA, "groq")["method"] == "external_provider.system_prompt"


@pytest.mark.parametrize("proof", [
    construir_prova_voz_assistida(MARKDOWN, "codex"),
    construir_prova_voz_humana(MARKDOWN, "Reinaldo Mendes"),
])
def test_content_sha256_incorreto_e_recusado_pelo_handoff(proof):
    adulterada = dict(proof, content_sha256="0" * 64)
    with pytest.raises(ValueError):
        validar_handoff_chatgpt(handoff_prova(adulterada))


def test_dna_padrao_pode_ser_explicito_ou_omisso():
    externa = construir_prova_voz_externa(PROMPT_SHA, "groq")
    assert externa == construir_prova_voz_externa(
        PROMPT_SHA, "groq", dna_prompt_sha256=DNA_PROMPT_SHA256)
    assert externa == construir_prova_voz_externa(
        PROMPT_SHA, "groq", dna_prompt_sha256=None)


@pytest.mark.parametrize("hash_invalido", ["abc", "A" * 64, "g" * 64, 123])
def test_hashes_mal_formados_sao_recusados(hash_invalido):
    with pytest.raises(ValueError):
        construir_prova_voz_externa(hash_invalido, "groq")
    for proof in (
        construir_prova_voz_assistida(MARKDOWN, "codex"),
        construir_prova_voz_humana(MARKDOWN, "Reinaldo Mendes"),
    ):
        with pytest.raises(ValueError):
            normalizar_aplicacao_voz(dict(proof, content_sha256=hash_invalido))
    with pytest.raises(ValueError):
        construir_prova_voz_externa(PROMPT_SHA, "groq", dna_prompt_sha256=hash_invalido)


@pytest.mark.parametrize("markdown", ["", "   ", "\n\t", None, 42])
def test_markdown_vazio_nunca_gera_prova(markdown):
    with pytest.raises(ValueError):
        construir_prova_voz_assistida(markdown, "codex")
    with pytest.raises(ValueError):
        construir_prova_voz_humana(markdown, "Reinaldo Mendes")


@pytest.mark.parametrize("proof", [
    construir_prova_voz_assistida(MARKDOWN, "codex"),
    construir_prova_voz_humana(MARKDOWN, "Reinaldo Mendes"),
    construir_prova_voz_externa(PROMPT_SHA, "groq"),
])
def test_edicao_do_markdown_invalida_qualquer_prova(proof):
    handoff = handoff_prova(proof)
    original = copy.deepcopy(handoff)
    atualizado = atualizar_handoff_revisao(handoff, EDITADO)
    assert atualizado["metadata"]["editorial_voice_application"] == normalizar_aplicacao_voz(None)
    assert "editorial_substance_review" not in atualizado["metadata"]
    assert atualizado["version_sha256"] != original["version_sha256"]
    assert validar_handoff_chatgpt(atualizado)["version_sha256"] == atualizado["version_sha256"]
    assert handoff == original  # a atualização não altera a versão de entrada


def test_edicao_mantem_not_applied_estavel():
    handoff = criar_handoff_chatgpt(artigo(), url_fonte=URL)
    assert handoff["metadata"]["editorial_voice_application"] == normalizar_aplicacao_voz(None)
    atualizado = atualizar_handoff_revisao(handoff, EDITADO)
    assert atualizado["metadata"]["editorial_voice_application"] == normalizar_aplicacao_voz(None)
    assert validar_handoff_chatgpt(atualizado)["valid"] is True


@pytest.mark.parametrize("proof", [
    construir_prova_voz_assistida(MARKDOWN, "codex"),
    construir_prova_voz_humana(MARKDOWN, "Reinaldo Mendes"),
    construir_prova_voz_externa(PROMPT_SHA, "groq"),
])
def test_prova_nunca_afirma_aprovacao_humana_ou_factual(proof):
    assert not (set(proof) & {"approved", "review_status", "publication_authorized", "factual"})
    assert not any("approv" in chave.lower() for chave in proof)
    handoff = handoff_prova(proof)
    assert handoff["metadata"]["review"] == {"approved": False}
    assert handoff["review_status"] == "PENDING_HUMAN_REVIEW"
    assert handoff["wordpress_written"] is False
    for claim in handoff["metadata"]["claims"]:
        assert claim["review_status"] == "PENDING_HUMAN_REVIEW"
