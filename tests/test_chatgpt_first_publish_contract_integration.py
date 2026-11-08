"""Integration regression: ChatGPT-first preview -> canonical package -> signed SEO.

No live WordPress and no real approval. The transition to ready here is a
synthetic test fixture. Only the Conexo OS reviewer can approve actual articles.
"""
import json
from pathlib import Path

import pytest

from mkt_flow_p0.editorial_core_offline import processar
from mkt_flow_p0.editorial_package_handoff import vincular_seo_antes_da_revisao
from mkt_flow_p0.seo_delivery_signing import prepare_signed_seo_contract

KEY = b"synthetic-offline-key-not-for-live-secret-00000000"
SLUG = "chatgpt-first-wordpress-teste"

def _input(tmp_path):
    meta = {
        "schema_version": "1.0",
        "article_id": "conexo-teste-integrado",
        "status": "aguardando_revisao",
        "title": "Como revisar metadados SEO antes de publicar no WordPress",
        "seo": {"title": "Como revisar SEO no WordPress",
                "description": "Entenda como conferir o contrato SEO antes da publicação.",
                "slug": SLUG},
        "sources": [{"name": "Documentação", "url": "https://wordpress.org/"}],
        "claims": [],
        "review": {"approved": False},
        "related_articles": [{"title": "Leitura relacionada",
                              "url": "https://conexotech.com.br/reviews/"}],
    }
    markdown = "## Contexto\n\n" + (
        "Este conteúdo é exclusivamente uma simulação editorial de teste sem alegações factuais. " * 20)
    metadata_file = tmp_path / "article.json"
    markdown_file = tmp_path / "article.md"
    metadata_file.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    markdown_file.write_text(markdown, encoding="utf-8")
    manifest = processar(metadata_file, markdown_file, tmp_path / "out")
    body = Path(manifest["wordpress_body"]).read_text(encoding="utf-8")
    unreviewed = {
        "schema_version": "editorial-workflow/2", "stage": "draft",
        "payload": {"title": meta["title"], "slug": SLUG, "content": body,
                    "sources": [{"url": "https://wordpress.org/"}]},
    }
    return manifest, body, unreviewed


def test_preview_then_handoff_then_signed_contract_only_with_synthetic_readback(tmp_path):
    manifest, body, unreviewed = _input(tmp_path)
    assert manifest["wordpress_written"] is False
    assert manifest["aprovacao_publicacao"] is False
    assert manifest["seo_wp_staging"]["approved_for_publication"] is False

    version = vincular_seo_antes_da_revisao(unreviewed, manifest, body)
    assert version["stage"] == "draft"
    assert "human_acceptance" not in version
    assert "reviews" not in version

    canonical = "https://conexotech.com.br/" + SLUG + "/"
    snapshot = {"ID": 9981, "post_type": "post", "post_status": "publish",
                "post_content": body, "post_title": version["payload"]["title"],
                "post_name": SLUG}
    response = {"intent": "publish", "status": "publish", "editorial_delivered": True,
                "retry_automatic": False, "version_sha256": version["version_sha256"],
                "post_id": 9981, "link": canonical, "snapshot": snapshot}
    with pytest.raises(ValueError, match="pacote editorial nao aprovado"):
        prepare_signed_seo_contract(version, response, seo_key=KEY)

    # Synthetic fixture only: proof that a separate approval is still required.
    ready = {**version, "stage": "ready"}
    signed = prepare_signed_seo_contract(ready, response, seo_key=KEY)
    assert signed["canonical"] == canonical
    assert signed["approved_for_publication"] is True
    assert signed["title"] == version["payload"]["seo"]["title"]

    # A post-publication mutation must not inherit the older SEO signature.
    response["snapshot"]["post_content"] += "mutated"
    with pytest.raises(ValueError, match="snapshot nao corresponde"):
        prepare_signed_seo_contract(ready, response, seo_key=KEY)


def test_changed_canonical_or_seo_requires_new_version(tmp_path):
    manifest, body, source = _input(tmp_path)
    version = vincular_seo_antes_da_revisao(source, manifest, body)
    assert version["version_sha256"]
    changed = json.loads(json.dumps(version))
    changed["payload"]["seo"]["description"] += " edição tardia"
    assert changed["version_sha256"] == version["version_sha256"]
    with pytest.raises(ValueError, match="SEO ja vinculado"):
        vincular_seo_antes_da_revisao(changed, manifest, body)
