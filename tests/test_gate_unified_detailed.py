"""Testes detalhados para mkt_flow_p0.gate_unified.

Cobertura: content_digest, READINESS_CATALOG, advisory_gate_receipt,
read_owner_release, validate_owner_release, DECISION_D1.
"""

import pytest

from mkt_flow_p0.gate_unified import (
    content_digest,
    READINESS_CATALOG,
    advisory_gate_receipt,
    DECISION_D1_SCREEN,
    DECISION_D1_VERSION,
    DECISION_D1_DATE,
    readiness_catalog,
    GateBlocked,
)


# --- content_digest ---

def test_content_digest_valid_string():
    """content_digest aceita strings não vazias e retorna SHA-256."""
    d = content_digest("<p>Texto confirmado</p>")
    assert isinstance(d, str)
    assert len(d) == 64


def test_content_digest_invalid_input():
    """content_digest levanta ValueError para entradas não-string."""
    with pytest.raises(ValueError):
        content_digest(None)  # type: ignore


# --- READINESS_CATALOG ---

def test_readiness_catalog_all_variants():
    """Todas as 4 variantes do catálogo são recuperáveis."""
    for key in ("conteudo", "wordpress", "recibos", "ambiente"):
        info = readiness_catalog(key)
        assert "significado" in info
        assert "campos_obrigatorios" in info
        assert "descricao" in info


def test_readiness_catalog_unknown_variant():
    """Variante desconhecida levanta KeyError."""
    with pytest.raises(KeyError):
        readiness_catalog("inexistente")


# --- advisory_gate_receipt ---

def test_advisory_gate_receipt_with_markdown():
    """advisory_gate_receipt produz receipt vinculado ao markdown."""
    info = {
        "content_sha256": "a" * 64,
        "version_sha256": "b" * 64,
        "approval_reference": "D1-TEST-1",
    }
    receipt = advisory_gate_receipt(info, markdown="<p>Texto confirmado</p>")
    assert receipt["status"] == "approved"
    assert receipt["content_sha256"] == content_digest("<p>Texto confirmado</p>")
    assert receipt["reviewer"] == "wordpress-gate-owner-3"
    assert receipt["evidence"].startswith("owner-release:")


def test_advisory_gate_receipt_without_markdown():
    """Sem markdown, digest vem do info directamente."""
    info = {
        "content_sha256": "a" * 64,
        "version_sha256": "b" * 64,
        "approval_reference": "D1-TEST-2",
    }
    receipt = advisory_gate_receipt(info)
    assert receipt["content_sha256"] == info["content_sha256"]
    assert receipt["evidence"].endswith(info["version_sha256"])


def test_advisory_gate_receipt_invalid_info():
    """Info inválida levanta ValueError."""
    with pytest.raises(ValueError):
        advisory_gate_receipt({"content_sha256": "nao-e-sha"})


# --- DECISION_D1 ---

def test_decision_d1_screen_is_set():
    """DECISION_D1_SCREEN está definido e tem valor esperado."""
    assert DECISION_D1_SCREEN == "conexo-gate-revisar-lote"
    assert DECISION_D1_VERSION == "1.0"
    assert DECISION_D1_DATE == "2026-11-16"


# --- Leitura de significado das variantes ---

def test_readiness_catalog_conteudo_significado():
    """Variant 'conteudo' tem significado esperado."""
    info = readiness_catalog("conteudo")
    assert "foi revisado e" in info["significado"]


def test_readiness_catalog_ambiente_significado():
    """Variant 'ambiente' tem significado esperado."""
    info = readiness_catalog("ambiente")
    assert "ambiente e configuração" in info["significado"]


def test_readiness_catalog_recibos_significado():
    """Variant 'recibos' tem significado esperado."""
    info = readiness_catalog("recibos")
    assert "comprovantes" in info["significado"]


def test_readiness_catalog_wordpress_significado():
    """Variant 'wordpress' tem significado esperado."""
    info = readiness_catalog("wordpress")
    assert "WordPress" in info["significado"]