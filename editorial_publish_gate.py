"""Guard local de compatibilidade e proveniencia para transicao WordPress.

O Gate WordPress continua sendo a autoridade de aceite humano. Este modulo
acrescenta verificacao fail-closed da marca de proveniencia e do parecer
independente. O registro do Revisor exige assinatura própria, distinta da
assinatura do certificado; callback isolado nunca constitui prova.
"""
import re
from pathlib import Path

from editorial_wordpress_readiness import validate_wordpress_readiness
from mkt_flow_p0.editorial_provenance import validar as validar_proveniencia


def _raw_field(value):
    if isinstance(value, dict):
        value = value.get("raw")
    return value if isinstance(value, str) and value.strip() else None


def _raw_content(post):
    if not isinstance(post, dict):
        return None
    content = post.get("content")
    if not isinstance(content, dict):
        return None
    return _raw_field(content)


def _readiness_snapshot(post):
    if not isinstance(post, dict):
        return post
    normalized = dict(post)
    for field in ("title", "content", "excerpt"):
        if isinstance(normalized.get(field), dict):
            normalized[field] = _raw_field(normalized[field])
    return normalized


def _matches_canonical_package_snapshot(post, payload):
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


def _review_blockers(post, certificate, signing_key, lookup_review,
                     registry_verification_key, *, now=None):
    if (not isinstance(certificate, dict)
            or not isinstance(signing_key, (bytes, bytearray))
            or not callable(lookup_review)
            or not isinstance(registry_verification_key, (bytes, bytearray))):
        return ["trusted_factual_review_missing"]
    try:
        from editorial_trusted_review import verify_independent_review
        result = verify_independent_review(
            post, certificate, bytes(signing_key), lookup_review,
            bytes(registry_verification_key), now=now)
    except Exception:
        return ["trusted_factual_review_verification_unavailable"]
    if isinstance(result, dict) and result.get("verified") is True:
        return []
    reason = result.get("reason") if isinstance(result, dict) else None
    reason = re.sub(r"[^a-z0-9_]+", "_", str(reason or "not_verified").lower())
    return ["trusted_factual_review_" + reason.strip("_")]


def authorize_publish(post, factual_review=None, *, package=None, core_root=None,
                      expected_category_id=10, owner_release=None,
                      review_certificate=None, review_signing_key=None,
                      lookup_review=None, registry_verification_key=None, now=None):
    problems = list(validate_wordpress_readiness(
        _readiness_snapshot(post), expected_category_id=expected_category_id).errors)

    body = _raw_content(post)
    if body is None:
        problems.append("editorial_provenance_content_raw_unavailable")
    else:
        provenance = validar_proveniencia(body)
        if not provenance["valido"]:
            problems.append("editorial_provenance_" + provenance.get("motivo", "invalid"))

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

    # Always verify, including when a canonical package is present.
    problems.extend(_review_blockers(
        post, review_certificate, review_signing_key, lookup_review,
        registry_verification_key, now=now))
    if not isinstance(factual_review, dict):
        problems.append("factual_review_missing")
    return {"autorizado": not problems, "bloqueios": _unique(problems)}


def _unique(items):
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
