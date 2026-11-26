"""Validação E1+E2 antes de qualquer escrita WordPress (contrato 2.3).

E1: GET autenticado `context=edit` (content.raw disponível).
E2: GET autenticado `context=view` (content.rendered completo).
Correlação: mesmo ID, mesmo status, mesmo hash de conteúdo bruto.

Este módulo não escreve nada. A chamada real depende de ambiente WordPress
autenticado; em testes é validado com sessão simulada (PASS SIMULADO).
"""
from __future__ import annotations

import hashlib

import requests

from mkt_flow_p0.editorial_transport import SITE


class E1E2Blocked(ValueError):
    """Levantado quando E1 ou E2 não podem ser confirmados."""


def _get(session, url, auth, timeout):
    try:
        response = session.get(url, auth=auth, timeout=timeout,
                               allow_redirects=False)
    except requests.RequestException:
        raise E1E2Blocked("E1E2_READ_OUTCOME_UNKNOWN") from None
    if response.status_code != 200:
        raise E1E2Blocked("E1E2_READ_HTTP_REJECTED")
    try:
        value = response.json()
    except (ValueError, TypeError):
        raise E1E2Blocked("E1E2_READ_INVALID_JSON") from None
    if not isinstance(value, dict):
        raise E1E2Blocked("E1E2_READ_INVALID_BODY")
    return value


def validate_e1_e2(post_id, wp_user, wp_app_password, *, session=requests,
                   timeout=15, expected_sha256=None):
    """Executa E1+E2 autenticados e correlaciona antes da escrita."""
    if not isinstance(post_id, int) or post_id < 1:
        raise E1E2Blocked("E1E2_POST_ID_INVALID")
    if not wp_user or not wp_app_password:
        raise E1E2Blocked("E1E2_CREDENTIALS_MISSING")
    auth = (wp_user, wp_app_password)
    base = f"{SITE.rstrip('/')}/wp-json/wp/v2/posts/{post_id}"

    e1 = _get(session, base + "?context=edit", auth, timeout)
    e2 = _get(session, base + "?context=view", auth, timeout)

    if e1.get("id") != post_id or e2.get("id") != post_id:
        raise E1E2Blocked("E1E2_POST_MISMATCH")
    if e1.get("status") != e2.get("status"):
        raise E1E2Blocked("E1E2_STATUS_MISMATCH")
    if e1.get("status") not in ("draft", "pending"):
        raise E1E2Blocked("E1E2_NOT_EDITABLE")
    raw = (e1.get("content") or {}).get("raw")
    rendered = (e2.get("content") or {}).get("rendered")
    if not isinstance(raw, str) or not raw.strip():
        raise E1E2Blocked("E1_RAW_CONTENT_MISSING")
    if not isinstance(rendered, str) or not rendered.strip():
        raise E1E2Blocked("E2_RENDERED_CONTENT_MISSING")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    if expected_sha256 and digest != expected_sha256:
        raise E1E2Blocked("E1_CONTENT_HASH_MISMATCH")
    # Correlação mínima: o texto renderizado deve conter o título do bruto.
    title = (e1.get("title") or {}).get("raw") or ""
    if title and title not in rendered:
        raise E1E2Blocked("E1E2_CONTENT_NOT_CORRELATED")
    return {"verified": True, "post_id": post_id, "status": e1["status"],
            "content_sha256": digest}
