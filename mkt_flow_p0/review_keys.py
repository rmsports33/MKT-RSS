"""Provisionamento das DUAS chaves separadas do fluxo de Revisor Único.

A chave do certificado e a chave de verificação do registro DEVEM ser distintas.
Este módulo apenas confirma disponibilidade (tamanho mínimo) e diferença —
nunca retorna, imprime ou registra os valores.
"""
from __future__ import annotations

import os

MIN_KEY_BYTES = 32


class ReviewKeyProvisioningBlocked(ValueError):
    """Levantado quando as chaves não estão corretamente provisionadas."""


def _read(name: str) -> bytes:
    value = os.environ.get(name, "")
    if not isinstance(value, str):
        return b""
    return value.strip().encode("utf-8")


def certificate_key() -> bytes:
    """Chave que assina o certificado factual (CONEXO_EDITORIAL_GATE_KEY)."""
    key = _read("CONEXO_EDITORIAL_GATE_KEY")
    if len(key) < MIN_KEY_BYTES:
        raise ReviewKeyProvisioningBlocked("CERTIFICATE_KEY_MISSING")
    return key


def registry_verification_key() -> bytes:
    """Chave SEPARADA que verifica o envelope do registro do Revisor."""
    key = _read("CONEXO_REVIEW_REGISTRY_KEY")
    if len(key) < MIN_KEY_BYTES:
        raise ReviewKeyProvisioningBlocked("REGISTRY_VERIFICATION_KEY_MISSING")
    return key


def keys_status() -> dict:
    """Resumo BOOLIANO do provisionamento. Nunca expõe valores."""
    cert = _read("CONEXO_EDITORIAL_GATE_KEY")
    reg = _read("CONEXO_REVIEW_REGISTRY_KEY")
    return {
        "certificate_key_available": len(cert) >= MIN_KEY_BYTES,
        "registry_key_available": len(reg) >= MIN_KEY_BYTES,
        "keys_are_distinct": bool(cert and reg and cert != reg),
        "safe_for_publication": bool(len(cert) >= MIN_KEY_BYTES
                                     and len(reg) >= MIN_KEY_BYTES
                                     and cert != reg),
    }
