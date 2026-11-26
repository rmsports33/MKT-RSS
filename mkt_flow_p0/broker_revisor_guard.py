"""Guarda do Revisor Único integrada ao caminho do broker MKT-RSS -> Gate V1.

Resolve o bloqueio `trusted_factual_review_broker_guard_not_integrated` do PR #130
sem remover nenhuma verificação de segurança.

Contrato:
- O certificado factual é verificado (HMAC do emissor) — existente.
- O registro do Revisor é buscado por adaptador autenticado (transporte).
- O envelope `{record, signature}` é verificado com chave SEPARADA da chave do
  certificado (HMAC-SHA256), conforme PR #129.
- Nenhuma chamada de rede é feita por este módulo: o adaptador é injetado.
- Falha em qualquer etapa => bloqueio fail-closed antes da escrita WordPress.

Este módulo não cria integração paralela: apenas fornece a guarda que o
`editorial_broker_transport.publish_via_broker` exige antes do POST.
"""
from __future__ import annotations

import hashlib
import hmac

from editorial_trusted_review import verify_independent_review


class BrokerReviewBlocked(ValueError):
    """Levantada antes de qualquer escrita no WordPress."""


def _canonical_bytes(value):
    import json
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def build_review_lookup(adapter, *, registry_verification_key):
    """Cria um adaptador de consulta que valida o envelope assinado.

    `adapter` deve ser callable(url) -> dict. O dict é tratado como transporte
    não confiável: somente um envelope `{record, signature}` com HMAC válido
    (chave separada) é aceito.
    """
    if not callable(adapter):
        raise BrokerReviewBlocked("trusted_review_adapter_missing")
    if (not isinstance(registry_verification_key, (bytes, bytearray))
            or len(registry_verification_key) < 32):
        raise BrokerReviewBlocked("registry_verification_key_invalid")
    key = bytes(registry_verification_key)

    def lookup(url):
        try:
            payload = adapter(url)
        except Exception:
            return {"error": "trusted_review_unavailable"}
        if not isinstance(payload, dict):
            return {"error": "review_record_missing"}
        record = payload.get("record")
        signature = payload.get("signature")
        if not isinstance(record, dict) or not isinstance(signature, str) or len(signature) != 64:
            return {"error": "review_record_signature_missing"}
        expected = hmac.new(key, _canonical_bytes(record), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return {"error": "review_record_signature_invalid"}
        return {"record": record, "signature": signature}

    return lookup


def require_broker_review(post, certificate, certificate_key, adapter,
                          registry_verification_key, *, now=None):
    """Exige parecer do Revisor Único antes da escrita via broker.

    Retorna {"verified": True} somente quando tudo é válido; caso contrário
    levanta BrokerReviewBlocked (fail-closed).
    """
    if not isinstance(certificate, dict):
        raise BrokerReviewBlocked("review_certificate_missing")
    if (not isinstance(certificate_key, (bytes, bytearray))
            or len(certificate_key) < 32):
        raise BrokerReviewBlocked("review_certificate_key_invalid")

    lookup = build_review_lookup(
        adapter, registry_verification_key=registry_verification_key)
    result = verify_independent_review(
        post, certificate, bytes(certificate_key), lookup,
        registry_verification_key=bytes(registry_verification_key), now=now)
    if not isinstance(result, dict) or result.get("verified") is not True:
        reason = result.get("reason") if isinstance(result, dict) else "not_verified"
        raise BrokerReviewBlocked("trusted_factual_review_" + str(reason))
    return {"verified": True, "reason": None}
