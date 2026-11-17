"""A origem pública do ConexoTech vive em um único módulo de constantes."""
import importlib
import pathlib

from mkt_flow_p0 import origins

MODULOS_COM_SITE = [
    "mkt_flow_p0.conexo_gate_trace",
    "mkt_flow_p0.conexo_remediation",
    "mkt_flow_p0.editorial_package_handoff",
    "mkt_flow_p0.seo_delivery_signing",
    "mkt_flow_p0.editorial_transport",
    "tools.produce_bank_article",
    "tools.wp_identity_preflight",
]


def test_origem_canonica_tem_esquema_e_host_coerentes():
    assert origins.SITE_ORIGIN == "https://conexotech.com.br"
    assert origins.SITE_HOST == "conexotech.com.br"
    assert origins.SITE_ORIGIN == "https://" + origins.SITE_HOST


def test_modulos_de_origem_compartilham_a_constante():
    for nome in MODULOS_COM_SITE:
        modulo = importlib.import_module(nome)
        assert modulo.SITE == origins.SITE_ORIGIN, nome


def test_modulo_de_host_usa_o_host_sem_esquema():
    modulo = importlib.import_module("mkt_flow_p0.editorial_readiness")
    assert modulo.SITE == origins.SITE_HOST


def test_readiness_wordpress_usa_o_host_canonico():
    modulo = importlib.import_module("editorial_wordpress_readiness")
    assert modulo.SITE_HOST == origins.SITE_HOST


def test_contrato_seo_exporta_a_origem_canonica():
    modulo = importlib.import_module("mkt_flow_p0.seo_contract_native")
    assert modulo.SITE_ORIGIN == origins.SITE_ORIGIN


def test_nenhum_modulo_redefine_a_origem_como_constante():
    """Fora de origins.py, a constante não pode ser escrita à mão de novo."""
    raiz = pathlib.Path(__file__).resolve().parent.parent
    infratores = []
    for caminho in raiz.rglob("*.py"):
        rel = caminho.relative_to(raiz).as_posix()
        if rel.startswith("tests/") or rel == "mkt_flow_p0/origins.py":
            continue
        if rel.startswith((".venv/", "node_modules/")):
            continue
        texto = caminho.read_text(encoding="utf-8", errors="replace")
        if 'SITE_ORIGIN = "https://conexotech.com.br"' in texto:
            infratores.append(rel)
    assert infratores == []
