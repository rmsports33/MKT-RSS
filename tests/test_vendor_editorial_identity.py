"""O consumidor vendorizado mantém autoria consistente sem copiar o contrato."""
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "redator-artigo-blogs/src/generator"


def load(name):
    spec = importlib.util.spec_from_file_location("vendor_" + name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_vendor_prompt_preserves_identity_and_avoids_example_prices():
    prompt = load("prompt").montar_system_prompt("audio")
    assert "Reinaldo Mendes" in prompt
    assert "evidência aprovada" in prompt
    assert not re.search(r"R\$\s*\d", prompt)


def test_vendor_final_html_has_human_author():
    page = load("render").montar_pagina(
        "Comparativo sintético", "Fixture sem publicação",
        [{"nome": "Fone A", "specs": {}, "fonte": "Fonte sintética"}],
        "audio", "<p>Prévia sintética.</p>",
    )
    schemas = [json.loads(s) for s in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', page, re.S)]
    assert any(s.get("author", {}).get("name") == "Reinaldo Mendes" for s in schemas)
