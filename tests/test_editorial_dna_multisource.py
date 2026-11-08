"""Contrato editorial comum: MKT-RSS produz, ChatGPT aprofunda; WP não é acionado."""
import hashlib
import json
import pytest

from mkt_flow_p0.editorial_identity import (
    DNA_EDITORIAL_PROMPT, criar_handoff_chatgpt, normalizar_fontes_complementares
)
from mkt_flow_p0.rewriter import SYSTEM_PROMPT, montar_prompt
from mkt_flow_p0.editorial_core_offline import validar_pacote


SOURCE = "https://example.org/noticia-original"
EXTRA = {
    "sources": [
        {"name": "Fonte oficial", "url": "https://www.example.com/documentacao",
         "facts": ["O aparelho aceita cartão microSD para expansão do armazenamento."]},
        {"name": "Análise independente", "url": "https://review.example.org/ensaio",
         "facts": ["A tela foi avaliada na comparação de configuração técnica."]}
    ]
}
ARTICLE = {
    "titulo_seo": "Comparativo de celulares sem frases genéricas",
    "slug": "comparativo-celulares",
    "meta_description": "Diferenças entre dois celulares explicadas com dados de fontes.",
    "texto_markdown": "## Comparação\n\n" + ("Cada diferença precisa ter uma fonte clara e útil para quem compra. " * 12)
}


def test_dna_is_used_by_actual_rewriter_not_duplicated_prompt():
    assert SYSTEM_PROMPT == DNA_EDITORIAL_PROMPT
    assert "ConexoTech" in SYSTEM_PROMPT
    assert "Conexo Insight" in SYSTEM_PROMPT
    assert "Evite frases genéricas" in SYSTEM_PROMPT


def test_multisource_prompt_is_attributed_and_marked_for_review():
    prompt = montar_prompt("Celulares", "Texto de origem", "Noticiário",
                           contexto_complementar=EXTRA)
    assert "https://www.example.com/documentacao" in prompt
    assert "https://review.example.org/ensaio" in prompt
    assert "NÃO aprovadas" in prompt
    assert "atribua cada informação" in prompt


def test_without_enrichment_legacy_prompt_still_works():
    prompt = montar_prompt("Celulares", "Texto original", "Noticiário")
    assert "Texto original" in prompt
    assert "Fontes complementares" not in prompt


def test_handoff_preserves_identity_origin_and_review_pending():
    packet = criar_handoff_chatgpt(ARTICLE, url_fonte=SOURCE,
                                   fonte_nome="Noticiário", contexto_complementar=EXTRA)
    m = packet["metadata"]
    assert packet["schema"] == "conexo-editorial-handoff/1"
    assert packet["wordpress_written"] is False
    assert packet["review_status"] == "PENDING_HUMAN_REVIEW"
    assert m["origin"] == {"system": "MKT-RSS", "source_url": SOURCE}
    assert m["editorial_identity"]["brand"] == "ConexoTech"
    assert m["editorial_identity"]["voice"] == "Conexo Insight"
    assert m["review"]["approved"] is False
    assert m["status"] == "aguardando_revisao"
    assert len(m["sources"]) == 3
    assert len(m["claims"]) == 2
    assert all(not c["evidence_ids"] for c in m["claims"])
    assert validar_pacote(m, packet["markdown"]) == []


def test_handoff_digest_changes_when_article_is_edited():
    before = criar_handoff_chatgpt(ARTICLE, url_fonte=SOURCE)
    after = criar_handoff_chatgpt(
        {**ARTICLE, "texto_markdown": ARTICLE["texto_markdown"] + " Outra análise."},
        url_fonte=SOURCE
    )
    assert before["metadata"]["article_id"] == after["metadata"]["article_id"]
    assert before["version_sha256"] != after["version_sha256"]


def test_original_source_is_not_duplicated():
    ctx = {"sources": [{"name": "Mesmo site", "url": SOURCE,
                        "facts": ["Informação adicional atribuída ao mesmo endereço."]}]}
    p = criar_handoff_chatgpt(ARTICLE, url_fonte=SOURCE, contexto_complementar=ctx)
    assert len(p["metadata"]["sources"]) == 1


@pytest.mark.parametrize("ctx", [
    {"sources": [{"name": "Risco", "url": "http://wrong.example/info",
                  "facts": ["Informação não segura em endereço HTTP."]}]},
    {"sources": [{"name": "Risco", "url": "https://user:secret@example.org/doc",
                  "facts": ["Credenciais nunca devem entrar em URLs."]}]},
    {"sources": [{"name": "Risco", "url": "https://other.example/doc",
                  "facts": ["curto"]}]},
    {"sources": [{"name": "Risco", "url": "https://other.example/doc",
                  "facts": ["Essa é uma informação que pede checagem."]},
                 {"name": "Duplicada", "url": "https://other.example/doc",
                  "facts": ["Outra informação com a mesma URL."]}]},
    {"sources": "uma lista inválida"},
    {"source": []},
])
def test_malformed_external_research_is_rejected_before_use(ctx):
    with pytest.raises(ValueError):
        normalizar_fontes_complementares(ctx)
    with pytest.raises(ValueError):
        montar_prompt("Título", "Corpo", contexto_complementar=ctx)


def test_no_mutation_of_external_sources():
    original = json.dumps(EXTRA, sort_keys=True)
    p = criar_handoff_chatgpt(ARTICLE, url_fonte=SOURCE, contexto_complementar=EXTRA)
    assert json.dumps(EXTRA, sort_keys=True) == original
    assert p["version_sha256"] == hashlib.sha256(
        json.dumps({"metadata": p["metadata"], "markdown": p["markdown"]},
                   sort_keys=True, ensure_ascii=False,
                   separators=(",", ":")).encode("utf-8")
    ).hexdigest()
