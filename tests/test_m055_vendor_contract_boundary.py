"""M05.5: detect vendor drift without importing a second factual contract.

Offline AST and filesystem checks. Does not call WP, LLM or marketplaces.
The canonical typed contract lives in bot-redator-artigo/src/editorial/contract.py.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "redator-artigo-blogs"
RSS = ROOT / "pipeline_rss.py"
COMPARATIVO = ROOT / "mkt_flow_p0" / "comparativo_flow.py"


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def test_vendor_render_exists_but_is_not_canonical_contract():
    assert (VENDOR / "src" / "generator" / "render.py").is_file()
    assert not (VENDOR / "src" / "editorial" / "contract.py").exists(), (
        "Contract v1.0 unexpectedly vendored: review duplicated ownership before merging"
    )


def test_rss_uses_local_evidence_adapter_not_vendor_editorial():
    imports = _imports(RSS)
    assert "mkt_flow_p0.adaptador_contrato_editorial" in imports
    assert "mkt_flow_p0.lastro_offline_noticia" in imports
    assert not any(mod.startswith("src.editorial") for mod in imports)


def test_comparativo_wp_is_separate_from_rss_wp():
    imports = _imports(COMPARATIVO)
    assert "mkt_flow_p0.comparativo_contract" in imports
    assert "mkt_flow_p0.wp_publisher" in imports
    assert "mkt_flow_p0.wp_publisher" not in _imports(RSS)


def test_vendor_must_not_be_silently_deleted():
    # Inventory guard: removing legacy renderer requires a reviewed migration.
    assert (VENDOR / "src" / "generator" / "render.py").is_file()
