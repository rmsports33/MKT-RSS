"""Compatibilidade do guard: flags do chamador não substituem o pacote canônico."""
from pathlib import Path
from editorial_wordpress_readiness import validate_wordpress_readiness


def authorize_publish(post, factual_review=None, *, package=None, core_root=None,
                      expected_category_id=10):
    from mkt_flow_p0.editorial_transport import load_core
    problems = list(validate_wordpress_readiness(post, expected_category_id=expected_category_id).errors)
    if not isinstance(package, dict) or not core_root:
        problems.append("canonical_editorial_package_missing")
    else:
        try:
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
        except (OSError, ValueError, TypeError, KeyError):
            problems.append("canonical_gate_unavailable_or_invalid")
    return {"autorizado": not problems, "bloqueios": problems}


def require_publish_authorization(post, factual_review=None, **kwargs):
    result = authorize_publish(post, factual_review, **kwargs)
    if not result["autorizado"]:
        raise PermissionError("publicacao_bloqueada: " + ", ".join(result["bloqueios"]))
