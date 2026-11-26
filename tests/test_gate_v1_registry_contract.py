"""Testes de comportamento do contrato do registro assinado (Gate V1 ↔ MKT-RSS).

Substitui os antigos testes que apenas procuravam strings no código.
"""
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))


def run_php_test():
    p = subprocess.run(
        ["php", str(BASE / "tests" / "test_gate_v1_registry_route.php")],
        cwd=str(BASE), capture_output=True, text=True, encoding="utf-8", timeout=30)
    return p


def test_teste_comportamental_php_aprovado():
    p = run_php_test()
    assert p.returncode == 0, p.stdout + p.stderr
    assert "FAIL: 0" in p.stdout
    assert "PASS: 16" in p.stdout


def test_patch_nao_modifica_core():
    patch = (BASE / "docs" / "patches" / "GATE_V1_REGISTRY_ASSINADO.md").read_text(encoding="utf-8")
    # O patch documenta uma linha aditiva no bootstrap e um include novo;
    # não deve pedir alteração de funções do core.
    assert "cxeg_quality_read" not in patch.split("## Arquivo novo")[0]
    assert "cxeg_standard_boot" in patch
