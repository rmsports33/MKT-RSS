"""Registro unico: todo documento de auditoria deve constar no documento mestre."""
import importlib.util
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]


def _carregar_modulo():
    caminho = RAIZ / "tools" / "check_registro_unico.py"
    spec = importlib.util.spec_from_file_location("check_registro_unico", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_registro_existe_e_referencia_os_documentos_de_auditoria():
    modulo = _carregar_modulo()
    assert modulo.faltantes() == [], (
        "Documentos de auditoria fora do registro unico: "
        + ", ".join(modulo.faltantes()))


def test_documentos_de_auditoria_foram_encontrados():
    modulo = _carregar_modulo()
    assert list(modulo.documentos_de_auditoria()), "nenhum documento de auditoria encontrado"


def test_prefixos_cobrem_auditorias_recentes():
    nomes = {p.name for p in (RAIZ / "docs").glob("*.md")}
    esperados = {
        "AUDITORIA_MODULOS_CREDENCIAIS_20261118.md",
        "CREDENCIAL_MOTOR_20261117.md",
        "GARGALO_RASCUNHO_WORDPRESS_20261117.md",
        "M07_FILA_CORRECAO_20261117.md",
        "M14_AUDITORIA_PRECOS_20261117.md",
        "PAUTAS_SELECIONADAS_20261117.md",
        "PAUTAS_TRIAGEM_20261117.md",
        "REGENERACAO_MOTOR_20261117.md",
        "TRIAGE_MECANISMO_CHATGPT_VS_OPENCODE_20261117.md",
    }
    assert esperados <= nomes
