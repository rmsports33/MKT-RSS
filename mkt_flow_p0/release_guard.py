"""Guardas única do caminho de publicação aprovada pelo proprietário.

Funções puras: sem rede, sem escrita, sem segredos. O lote e a janela agendada
importam daqui para que a guarda não divirja entre os dois pontos de entrada.
"""
import json
import os
import re

_VERSION = re.compile(r"[a-f0-9]{64}\Z")


def is_current_version(value):
    """True somente para um SHA-256 hex completo de 64 caracteres."""
    return isinstance(value, str) and _VERSION.fullmatch(value) is not None


def preflight_approved(preflight, post_id, version):
    """True somente para pré-voo validado, sem escrita e da versão exata."""
    return (isinstance(preflight, dict)
            and preflight.get("validated") is True
            and preflight.get("post_id") == post_id
            and preflight.get("version_sha256") == version
            and preflight.get("write") is False)


def publication_verified(result, post_id):
    """True somente para publicação gravada, confirmada e com SEO público lido."""
    return (isinstance(result, dict) and "erro" not in result
            and result.get("verified") is True
            and result.get("post_id") == post_id
            and result.get("seo_public_verified") is True)


def emit(result, heading):
    """Imprime o JSON seguro e espelha no resumo do Actions, quando existir."""
    safe = json.dumps(result, ensure_ascii=False, sort_keys=True)
    print(safe)
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as out:
            out.write(heading + "\n\n" + safe + "\n")
    return safe
