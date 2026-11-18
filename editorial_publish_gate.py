"""Guard local de compatibilidade e proveniencia para transicao WordPress.

O Gate WordPress continua sendo a autoridade de aceite humano. Este modulo
acrescenta uma verificacao fail-closed da marca de proveniencia no corpo bruto
persistido; uma marca valida nunca substitui owner_release nem revisao factual.
"""
from pathlib import Path

from editorial_wordpress_readiness import validate_wordpress_readiness
from mkt_flow_p0.editorial_provenance import validar as validar_proveniencia


def _raw_field(value):
    """Resolve only editable raw content; rendered HTML is never a version source."""
    if isinstance(value, dict):
        value = value.get("raw")
    return value if isinstance(value, str) and value.strip() else None


def _raw_content(post):
    if not isinstance(post, dict):
        return None
    return _raw_field(post.get("content"))


def _readiness_snapshot(post):
    """Normalize REST objects for readiness without falling back to rendered values."""
    if not isinstance(post, dict):
        return post
    normalized = dict(post)
    for field in ("title", "content", "excerpt"):
        if isinstance(normalized.get(field), dict):
            normalized[field] = _raw_field(normalized[field])
    return normalized


def _matches_canonical_package_snapshot(post, payload):
    """Compare canonical package identity against persisted raw REST fields."""
    if not isinstance(post, dict) or not isinstance(payload, dict):
        return False
    wordpress = payload.get("wordpress")
    if not isinstance(wordpress, dict):
        return False
    remote = _readiness_snapshot(post)
    expected = {
        "id": wordpress.get("post_id"),
        "title": payload.get("title"),
        "slug": payload.get("slug"),
        "featured_media": wordpress.get("featured_media"),
        "categories": wordpress.get("categories"),
    }
    return (
        isinstance(remote, dict)
        and all(remote.get(key) == value for key, value in expected.items())
        and _raw_content(post) == payload.get("content")
    )


def authorize_publish(post, factual_review=None, *, package=None, core_root=None,
                      expected_category_id=10, owner_release=None):
    problems = list(validate_wordpress_readiness(
        _readiness_snapshot(post), expected_category_id=expected_category_id).errors)

    # Proveniencia obrigatoria: conferir o corpo bruto persistido, nunca o
    # HTML rendered nem uma flag enviada pelo chamador.
    body = _raw_content(post)
    if body is None:
        problems.append("editorial_provenance_content_raw_unavailable")
    else:
        provenance = validar_proveniencia(body)
        if not provenance["valido"]:
            problems.append("editorial_provenance_" + provenance.get("motivo", "invalid"))

    # Autorizacao humana: o Gate do WordPress e a unica autoridade. O recibo
    # e lido do servidor (nunca um hash colado) e precisa estar vinculado a
    # versao exata do rascunho.
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
            if body is not None and content_digest(body) != info["content_sha256"]:
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
            errors, blockers = core.validator().evaluate(
                package, Path(core_root), require_editorial_ready=True)
            problems.extend(errors + blockers)
            p = package["payload"]
            if package.get("stage") != "ready":
                problems.append("version_not_ready")
            if not _matches_canonical_package_snapshot(post, p):
                problems.append("remote_version_mismatch")
        except (ImportError, OSError, ValueError, TypeError, KeyError, RuntimeError):
            problems.append("canonical_gate_unavailable_or_invalid")
    return {"autorizado": not problems, "bloqueios": _unique(problems)}


def _unique(items):
    """Mantem a ordem e remove bloqueios repetidos."""
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
