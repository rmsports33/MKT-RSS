"""Compatibilidade do guard: flags do chamador não substituem o pacote canônico.

Este módulo deixou de ser um "gate paralelo": ele apenas agrega os bloqueios
existentes e **exige o aceite humano emitido pelo Gate do WordPress**
(``owner_release``). Sem esse recibo, a publicação continua bloqueada — um
check técnico nunca vira aprovação.
"""
from pathlib import Path
from editorial_wordpress_readiness import validate_wordpress_readiness


def authorize_publish(post, factual_review=None, *, package=None, core_root=None,
                      expected_category_id=10, owner_release=None):
    problems = list(validate_wordpress_readiness(post, expected_category_id=expected_category_id).errors)
    # Autorização humana: o Gate do WordPress é a única autoridade. O recibo
    # é lido do servidor (nunca um hash colado) e precisa estar vinculado à
    # versão exata do rascunho.
    if owner_release is None:
        problems.append("gate_owner_release_missing")
    else:
        try:
            from mkt_flow_p0.gate_unified import content_digest, validate_owner_release
            info = validate_owner_release(owner_release)
        except (ValueError, TypeError, KeyError, ImportError):
            problems.append("gate_owner_release_invalid")
        else:
            post_id = post.get("id") if isinstance(post, dict) else None
            if post_id is not None and info["post_id"] != post_id:
                problems.append("gate_owner_release_post_mismatch")
            body = post.get("content") if isinstance(post, dict) else None
            if isinstance(body, str) and content_digest(body) != info["content_sha256"]:
                problems.append("remote_version_mismatch")
    if not isinstance(package, dict) or not core_root:
        problems.append("canonical_editorial_package_missing")
        problems.append("trusted_factual_review_missing")
        if not isinstance(factual_review, dict):
            problems.append("factual_review_missing")
    else:
        try:
            from mkt_flow_p0.editorial_transport import load_core
            core = load_core(core_root)
            errors, blockers = core.validator().evaluate(package, Path(core_root), require_editorial_ready=True)
            problems.extend(errors + blockers)
            p = package["payload"]
            wp = p["wordpress"]
            if package.get("stage") != "ready":
                problems.append("version_not_ready")
            if not isinstance(post, dict) or any(post.get(key) != expected for key, expected in {
                    "id": wp["post_id"], "title": p["title"], "content": p["content"],
                    "slug": p["slug"], "featured_media": wp["featured_media"],
                    "categories": wp["categories"]}.items()):
                problems.append("remote_version_mismatch")
        except (ImportError, OSError, ValueError, TypeError, KeyError, RuntimeError):
            problems.append("canonical_gate_unavailable_or_invalid")
    return {"autorizado": not problems, "bloqueios": _unique(problems)}


def _unique(items):
    """Mantém a ordem e remove bloqueios repetidos."""
    seen, out = set(), []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def require_publish_authorization(post, factual_review=None, **kwargs):
    result = authorize_publish(post, factual_review, **kwargs)
    if not result["autorizado"]:
        raise PermissionError("publicacao_bloqueada: " + ", ".join(result["bloqueios"]))
