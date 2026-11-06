"""Handoff real: versionamento, revisão pendente, disco e CLI offline.

Não usa Groq, GitHub Actions nem WordPress.
"""
import json
from copy import deepcopy

import pytest

from mkt_flow_p0.editorial_identity import (
    criar_handoff_chatgpt, salvar_handoff_chatgpt, validar_handoff_chatgpt,
)

URL = "https://developer.android.com/blog/posts/android-intelligence-system-in-app-agents-ads"
CONTEXT = {"sources": [{"name": "Android Developers", "url": "https://developer.android.com/ai/appfunctions",
                       "facts": ["O AppFunctions permite aos aplicativos expor ações específicas."]}]}
ART = {
    "titulo_seo": "Android: apps com agentes e suas funções",
    "meta_description": "Guia técnico para entender o uso de agentes em aplicativos Android.",
    "slug": "android-appfunctions-agentes",
    "texto_markdown": "## Contexto\n\n" + ("A função precisa ser demonstrada em documentação oficial. " * 19),
}


def make():
    return criar_handoff_chatgpt(ART, url_fonte=URL, fonte_nome="Android Developers",
                                 contexto_complementar=CONTEXT)


def test_handoff_can_be_verified_without_network():
    r = validar_handoff_chatgpt(make())
    assert r["valid"] is True
    assert r["source_count"] == 2
    assert r["claims_pending"] == 1
    assert r["review_status"] == "PENDING_HUMAN_REVIEW"


@pytest.mark.parametrize("change", [
    lambda h: h.update(markdown=h["markdown"] + " Texto alterado."),
    lambda h: h.update(version_sha256="0" * 64),
    lambda h: h.update(review_status="APPROVED"),
    lambda h: h.update(wordpress_written=True),
    lambda h: h["metadata"]["review"].update(approved=True),
    lambda h: h["metadata"].update(status="revisado"),
    lambda h: h["metadata"]["origin"].update(source_url="https://example.net/unrelated"),
    lambda h: h["metadata"]["sources"].append(deepcopy(h["metadata"]["sources"][0])),
    lambda h: h["metadata"]["claims"][0].update(review_status="PASS"),
    lambda h: h["metadata"]["claims"][0].update(source_urls=["https://other.example/doc"]),
    lambda h: h["metadata"]["editorial_identity"].update(brand="Outro site"),
])
def test_stale_or_promoted_handoff_rejected(change):
    h = make()
    change(h)
    with pytest.raises(ValueError):
        validar_handoff_chatgpt(h)


def test_writer_is_idempotent_but_never_overwrites(tmp_path):
    h = make()
    f = salvar_handoff_chatgpt(h, tmp_path / "pacotes")
    assert f == salvar_handoff_chatgpt(h, tmp_path / "pacotes")
    assert len(list((tmp_path / "pacotes").glob("*.json"))) == 1
    assert json.loads(open(f, encoding="utf-8").read())["version_sha256"] == h["version_sha256"]
    # An editor change produces an independent version, not a reuse of approval.
    new = criar_handoff_chatgpt({**ART, "texto_markdown": ART["texto_markdown"] + "\nNovo parágrafo."},
                                url_fonte=URL, contexto_complementar=CONTEXT)
    f2 = salvar_handoff_chatgpt(new, tmp_path / "pacotes")
    assert f2 != f
    assert len(list((tmp_path / "pacotes").glob("*.json"))) == 2


def test_existing_file_cannot_be_silently_corrupted(tmp_path):
    h = make()
    file = salvar_handoff_chatgpt(h, tmp_path)
    with open(file, "w", encoding="utf-8") as f:
        f.write("{}")
    with pytest.raises(ValueError, match="não corresponde"):
        salvar_handoff_chatgpt(h, tmp_path)


def test_pilot_package_from_previous_session_is_compatible():
    """Only run when the prior pilot fixture is available; no mandatory data."""
    from pathlib import Path
    pilot = Path("tests/fixtures/editorial_multisource_android.json")
    if not pilot.exists():
        pytest.skip("fixture do piloto não incluída no checkout")
    result = validar_handoff_chatgpt(json.loads(pilot.read_text(encoding="utf-8")))
    assert result["source_count"] == 3
    assert result["claims_pending"] == 6
