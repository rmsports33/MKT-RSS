"""Verified GitHub Actions operator policy for supervised P1 decisions.

Never trust a free-form --operador value as proof of identity.
The GitHub Actions runner environment is a *claim*, not a cryptographic attestation:
only use it inside a trusted, restricted workflow (not pull_request) with an
environment approval gate and an explicit allowlist.
"""
import os
import re


def operador_autorizado(*, expected_repository="rmsports33/MKT-RSS"):
    env = os.environ
    actor = env.get("GITHUB_ACTOR", "")
    allowed = [x.strip() for x in env.get("P1_AUTHORIZED_ACTORS", "").split(",") if x.strip()]
    if not allowed or not re.fullmatch(r"[A-Za-z0-9-]{1,39}", actor):
        raise PermissionError("P1: identidade/allowlist ausente")
    if actor.lower() not in {x.lower() for x in allowed}:
        raise PermissionError("P1: operador nao autorizado")
    if (env.get("GITHUB_REPOSITORY") != expected_repository
            or env.get("GITHUB_REF") != "refs/heads/master"
            or env.get("GITHUB_EVENT_NAME") != "workflow_dispatch"):
        raise PermissionError("P1: contexto GitHub nao autorizado")
    return actor
