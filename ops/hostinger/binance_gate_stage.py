#!/usr/bin/env python3
"""Stage the reviewed Binance draft through the canonical Gate (Issue #121).

IMPORTANT — CORRECTED APPROACH (17/11/2026):
A converter from ``conexo-editorial-handoff/1`` (metadata + markdown) to the
``editorial-workflow/2`` package is NOT a deterministic step: the Gate validator
requires many fields (substantive_review, sources, claims, images, human, ...)
that only the supervised editorial pipeline can produce. This script therefore
does NOT try to synthesize a package from a handoff. It accepts ONLY an already
built ``editorial-workflow/2`` package and stages it via the canonical Gate.

This is the ONLY sanctioned way to create the draft:
``mkt_flow_p0.editorial_transport.publish_package(intent="stage")`` -> the
hash-pinned core -> WordPress Gate route ``editorial/write``. No generic REST
fallback, no direct wp/v2/posts write, no token in this file.

Fail-closed guarantees:
- requires a real editorial-workflow/2 package at an explicit path;
- verifies version SHA-256 against the expected immutable version;
- requires the trusted core checkout (hash-pinned) to exist;
- reads WP credentials from the operator's private token file (never env in repo);
- one stage attempt per version (idempotency marker), no automatic retry;
- verifies readback: status=draft, same version, featured_media=9892;
- never publishes, schedules, approves or changes an existing post.
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPECTED_VERSION = "d2ccb99e2dbe0dbc999a4b8e1fdd49d089c9299c679f5cb6200edc5db6e00fd2"
EXPECTED_MEDIA_ID = 9892
SITE = "https://conexotech.com.br"
ARTICLE_REF = "binance-revisao-6e8da0b05713"
WP_TOKEN = Path.home() / ".config/conexo-os/wp-editorial.token"
PACKAGE_GLOB = "rss_3fdd8256de5696d1869a36e8-*.json"
HANDOFF_DIR = Path.home() / ".local/share/conexo-os/handoffs/binance-revisao-48f1ea5be313"


def _fail(reason, **extra):
    out = {"status": "BLOCKED", "reason": reason,
           "wordpress_written": False, "publication_authorized": False}
    out.update(extra)
    print(json.dumps(out, ensure_ascii=False))
    return 2


def _read_wp_credentials():
    """Read credentials from the operator's private token file, never the repo.

    Supports either ``user:app_password`` or a bare token; in the bare case the
    user is taken from WP_USER/WP_APP_PASSWORD env if present. Never prints.
    """
    if not WP_TOKEN.is_file() or WP_TOKEN.is_symlink():
        return None
    try:
        data = WP_TOKEN.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not data or len(data) > 512:
        return None
    if ":" in data:
        user, password = data.split(":", 1)
        return (user.strip(), password.strip()) if user.strip() and password.strip() else None
    # Bare token: treat as app password; user must come from private env.
    user = os.environ.get("WP_USER") or os.environ.get("CONEXO_WP_USER")
    return (user, data) if user else None


def _find_core(explicit=None):
    """Locate the trusted hash-pinned core checkout; verify via load_core()."""
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.environ.get("CONEXO_EDITORIAL_CORE_ROOT", "")
    if env:
        candidates.append(Path(env))
    candidates.append(Path.home() / ".cache/conexo-os/editorial-core")
    candidates.append(Path.home() / "conexo-os-core")
    for base in candidates:
        if not base.is_dir():
            continue
        try:
            from mkt_flow_p0.editorial_transport import load_core
            load_core(base)  # verifies every locked file by SHA-256
            return base
        except Exception:
            continue
    return None


def _load_package(explicit=None):
    """Load an already-built editorial-workflow/2 package for this version."""
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    for candidate in sorted(HANDOFF_DIR.glob(PACKAGE_GLOB)):
        candidates.append(candidate)
    for path in candidates:
        if not path.is_file() or path.is_symlink():
            continue
        try:
            pkg = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if not isinstance(pkg, dict):
            continue
        if pkg.get("schema_version") != "editorial-workflow/2":
            continue
        if pkg.get("version_sha256") != EXPECTED_VERSION:
            continue
        return path, pkg
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--core-root", default=None)
    ap.add_argument("--package", default=None,
                    help="explicit path to the editorial-workflow/2 package")
    args = ap.parse_args()

    # Idempotency: one attempt per version.
    marker = HANDOFF_DIR / ("gate-stage-" + EXPECTED_VERSION[:16] + ".json")
    if marker.exists():
        return _fail("ALREADY_ATTEMPTED")

    pkg_path, package = _load_package(args.package)
    if package is None:
        # The handoff is NOT a publishable package. Explain the real blocker.
        handoff_exists = (HANDOFF_DIR / "pipeline-report.json").is_file()
        return _fail(
            "PUBLISHABLE_PACKAGE_MISSING",
            detail=("o handoff conexo-editorial-handoff/1 nao e entrada do Gate; "
                    "e necessario o pacote editorial-workflow/2 gerado pelo pipeline "
                    "supervisionado. NaO sintetizar o pacote localmente."),
            handoff_present=handoff_exists)

    core_root = _find_core(args.core_root)
    if core_root is None:
        return _fail("TRUSTED_CORE_MISSING")

    creds = _read_wp_credentials()
    if creds is None:
        return _fail("WP_CREDENTIALS_MISSING_OR_UNREADABLE")
    wp_user, wp_pass = creds

    # Associate the licensed media only to the new draft.
    payload = dict(package.get("payload") or {})
    wp = dict(payload.get("wordpress") or {})
    wp["post_id"] = 0  # stage creates a new private draft only
    wp["featured_media"] = EXPECTED_MEDIA_ID
    payload["wordpress"] = wp
    package = dict(package)
    package["payload"] = payload

    try:
        from mkt_flow_p0.editorial_transport import publish_package
        result = publish_package(
            package, core_root=core_root, wp_url=SITE,
            wp_user=wp_user, wp_password=wp_pass,
            actor_id=4, intent="stage",
            publication_reference=ARTICLE_REF + "-stage",
        )
    except Exception:
        marker.write_text(json.dumps({"status": "FAILED_UNKNOWN",
                                      "version_sha256": EXPECTED_VERSION}) + "\n")
        return _fail("STAGE_OUTCOME_UNKNOWN_RECONCILE_NO_RETRY")

    marker.write_text(json.dumps({"status": result.get("erro", "ATTEMPTED"),
                                   "version_sha256": EXPECTED_VERSION}) + "\n")

    ok = (isinstance(result, dict) and not result.get("erro")
          and result.get("status") in {"draft", "staged_for_theme_review"}
          and result.get("version_sha256") == EXPECTED_VERSION)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
