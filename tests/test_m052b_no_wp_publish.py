"""M05.2B: impedir reintroducao de publicacao WordPress sem gate factual.

Teste estatico offline: nao depende de rede, WP, LLM ou credenciais.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "pipeline_rss.py"


def test_rss_pipeline_nao_invoca_publicador_wordpress():
    tree = ast.parse(PIPELINE.read_text(encoding="utf-8"))
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "publicar_no_wordpress"
    ]
    assert not calls, "RSS nao pode publicar sem certificacao factual"


def test_rss_pipeline_nao_importa_publicador_wordpress():
    tree = ast.parse(PIPELINE.read_text(encoding="utf-8"))
    imports = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "mkt_flow_p0.wp_publisher"
    ]
    assert not imports, "RSS nao pode reativar o publicador por import"


def test_rss_pipeline_conserva_bloqueio_factual():
    tree = ast.parse(PIPELINE.read_text(encoding="utf-8"))
    fn = next(
        n for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name == "processar_item"
    )
    values = [
        node.value for node in ast.walk(fn)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    assert "gate_factual_pos_ia_nao_integrado" in values
    assert "NAO_VERIFICADO" in values
