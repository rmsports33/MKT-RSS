"""Static contract: experimental operational entry must remain offline-only."""
from pathlib import Path
import ast

def test_operational_entry_is_the_only_public_pilot_dispatch():
    code = Path("mkt_flow_p0/editorial_pilot.py").read_text(encoding="utf-8")
    tree = ast.parse(code)
    fns = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert "run_operational" in fns
    body = ast.get_source_segment(code, fns["run_operational"])
    assert "callback_legado_desativado" in body
    assert "run_offline" in body
    assert "generate(" not in body

def test_real_provider_entry_denies_by_default():
    code = Path("mkt_flow_p0/editorial_offline_adapter.py").read_text(encoding="utf-8")
    tree = ast.parse(code)
    fns = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert "authorize_provider" in fns
    body = ast.get_source_segment(code, fns["authorize_provider"])
    assert "isolamento_de_rede_nao_certificado" in body
    assert "BLOQUEADO" in body
