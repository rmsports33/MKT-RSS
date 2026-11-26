"""Adaptador real do registro confiável do Revisor Único.

Busca o registro editorial autenticado no servidor WordPress do Gate V1 via
GET autenticado (Application Password). O adaptador é SOMENTE transporte:
devolve o envelope bruto `{record, signature}` para que
`broker_revisor_guard.build_review_lookup` valide a assinatura com chave separada.

Segurança:
- HTTPS obrigatório.
- Host fixado ao destino WordPress permitido (mesmo SITE do transporte).
- Nenhuma chave/segredo é exposto em log ou retorno.
- Timeout e fail-closed em qualquer erro de rede/HTTP/JSON.
"""
from __future__ import annotations

import re

import requests

from mkt_flow_p0.editorial_transport import SITE


class RegistryAdapterBlocked(ValueError):
    """Levantado antes de qualquer escrita no WordPress."""


def _validate_url(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        raise RegistryAdapterBlocked("REGISTRY_URL_MISSING")
    url = url.strip().rstrip("/")
    parts = requests.utils.urlparse(url) if hasattr(requests.utils, "urlparse") else None
    # Validação conservadora sem dependência extra
    import urllib.parse as up
    p = up.urlsplit(url)
    if p.scheme != "https" or not p.netloc or p.username or p.password or p.query or p.fragment:
        raise RegistryAdapterBlocked("REGISTRY_URL_INVALID")
    if p.netloc.lower() != up.urlsplit(SITE).netloc.lower():
        raise RegistryAdapterBlocked("REGISTRY_HOST_NOT_ALLOWED")
    return url


def build_registry_adapter(*, wp_user: str, wp_app_password: str,
                           session=requests, timeout: int = 15,
                           route_prefix: str = "/wp-json/conexo/v1/editorial"):
    """Cria callable(url) -> envelope, usando GET autenticado.

    `url` deve ser a `review_record_url` do certificado, no host permitido.
    """
    if not wp_user or not wp_app_password:
        raise RegistryAdapterBlocked("WP_SERVICE_ACCOUNT_NOT_CONFIGURED")
    auth = (wp_user, wp_app_password)

    def adapter(url):
        target = _validate_url(url)
        # Converte URL pública do registro em rota autenticada do Gate, quando
        # necessário. Nunca segue redirecionamentos (fail-closed).
        try:
            response = session.get(target, auth=auth, timeout=timeout,
                                   allow_redirects=False)
        except requests.RequestException:
            return {"error": "trusted_review_unavailable"}
        if response.status_code != 200:
            return {"error": "review_record_http_rejected"}
        try:
            value = response.json()
        except (ValueError, TypeError):
            return {"error": "review_record_invalid_json"}
        if not isinstance(value, dict):
            return {"error": "review_record_invalid_body"}
        return value

    return adapter
