"""Central WordPress destination resolution — fail-closed, no production fallback.

Regras (decisão 25/11/2026):
  * `rss-homolog` é um ambiente de VALIDAÇÃO, não um WordPress de homologação.
    O staging Hostinger foi descontinuado e NÃO será reativado.
  * Nenhum transporte, publicador ou workflow pode presumir
    `https://conexotech.com.br` como destino de escrita.
  * Se a configuração estiver ausente, inválida ou incompatível com a operação,
    a resolução falha antes de qualquer chamada REST.
  * Escrita em produção (`draft`/`publish`/`schedule`) exige autorização
    operacional explícita via `WP_OPERATION_MODE=production` e credenciais
    próprias, todas presentes.

Este módulo NÃO faz chamadas de rede. Apenas resolve e valida configuração.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlsplit

# Domínio canônico de PRODUÇÃO — usado apenas para canonical/SEO/validação de
# links. NUNCA como destino de escrita implícito.
CANONICAL_SITE = "https://conexotech.com.br"

# Ambiente GitHub que significa VALIDAÇÃO (não escrita WordPress).
VALIDATION_ENVIRONMENT = "rss-homolog"

# Modos operacionais explícitos.
OPERATION_VALIDATE = "validate"
OPERATION_DRAFT = "draft"
OPERATION_PUBLISH = "publish"

_WRITE_OPERATIONS = frozenset((OPERATION_DRAFT, OPERATION_PUBLISH))
_PRODUCTION_MODE = "production"


class DestinationBlocked(ValueError):
    """Raised before any network call when destination config is not safe."""


@dataclass(frozen=True)
class WpDestination:
    url: str
    user: str
    password: str
    environment: str
    operation: str

    @property
    def auth(self):
        return (self.user, self.password)


def _clean(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _valid_https_url(value: str) -> bool:
    try:
        parts = urlsplit(value)
    except ValueError:
        return False
    return (parts.scheme == "https" and bool(parts.netloc)
            and not parts.username and not parts.password
            and parts.query == "" and parts.fragment == "")


def resolve(operation: str, *, env: dict | None = None) -> WpDestination:
    """Resolve the WordPress destination for `operation` or fail closed.

    `operation` must be one of OPERATION_VALIDATE, OPERATION_DRAFT,
    OPERATION_PUBLISH (schedule is treated as publish).

    Validation operations NEVER return a WordPress destination: there is no
    staging WordPress. They must fail before any REST call that could write.
    """
    environ = os.environ if env is None else env
    op = environ.get("WP_OPERATION", operation).strip() if operation \
        else environ.get("WP_OPERATION", "").strip()

    if op not in (OPERATION_VALIDATE, OPERATION_DRAFT, OPERATION_PUBLISH):
        raise DestinationBlocked("OPERATION_NOT_RECOGNIZED")

    github_env = environ.get("GITHUB_ENVIRONMENT", "").strip()

    # rss-homolog is validation only. No staging WP exists anymore.
    if github_env == VALIDATION_ENVIRONMENT or op == OPERATION_VALIDATE:
        raise DestinationBlocked(
            "VALIDATION_ENVIRONMENT_HAS_NO_WORDPRESS_DESTINATION"
        )

    if op not in _WRITE_OPERATIONS:
        raise DestinationBlocked("OPERATION_NOT_WRITABLE")

    # Explicit independent production authorization is mandatory for any write.
    if environ.get("WP_OPERATION_MODE", "").strip() != _PRODUCTION_MODE:
        raise DestinationBlocked("PRODUCTION_WRITE_NOT_AUTHORIZED")

    url = environ.get("WP_URL", "").strip().rstrip("/")
    user = environ.get("WP_USER", "").strip()
    password = environ.get("WP_APP_PASSWORD", "")  # preserve exact chars

    if not url or not user or not password:
        raise DestinationBlocked("WP_DESTINATION_INCOMPLETE")
    if not _valid_https_url(url):
        raise DestinationBlocked("WP_DESTINATION_URL_INVALID")
    if url != CANONICAL_SITE:
        raise DestinationBlocked("WP_DESTINATION_NOT_AUTHORIZED")

    return WpDestination(
        url=url,
        user=user,
        password=password,
        environment=github_env or "unspecified",
        operation=op,
    )


def assert_writable(destination: WpDestination, operation: str) -> None:
    """Last guard before a REST write. Refuses validation context entirely."""
    if destination.operation != operation:
        raise DestinationBlocked("OPERATION_MISMATCH")
    if operation not in _WRITE_OPERATIONS:
        raise DestinationBlocked("OPERATION_NOT_WRITABLE")
    if destination.url.rstrip("/") != CANONICAL_SITE:
        raise DestinationBlocked("WP_DESTINATION_NOT_AUTHORIZED")
