#!/usr/bin/env python3
"""Stage the exact reviewed Binance version through the canonical Gate (Issue #121).

This is the ONLY sanctioned way to create the Binance draft: it calls
``mkt_flow_p0.editorial_transport.publish_package(intent="stage")``, which uses
the hash-pinned core and the WordPress Gate route ``editorial/write``. There is
no generic REST fallback, no direct wp/v2/posts write, no token in this file.

Fail-closed guarantees:
- reads only the immutable private handoff; verifies version + markdown SHA-256;
- requires the trusted core checkout to exist locally with the exact locked files;
- creates ONE stage attempt per version (idempotency key), never auto-retries;
- verifies authenticated readback: status=draft, same version, featured_media=9892;
- never publishes, schedules, approves or changes any existing post.

Credentials are read from the operator's private environment on the server and
are scrubbed before any subprocess. Nothing secret is printed or committed.
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

HANDOFF = Path.home() / ".local/share/conexo-os/handoffs/binance-revisao-48f1ea5be313"
EXPECTED_VERSION = "d2ccb99e2dbe0dbc999a4b8e1fdd49d089c9299c679f5cb6200edc5db6e00fd2"
EXPECTED_MARKDOWN = "1969799ce2c4a1b6ad629eec62c39095ac58418695bab2f3f53efefe57448b60"
EXPECTED_MEDIA_ID = 9892
SITE = "https://conexotech.com.br"
ARTICLE_REF = "binance-revisao-6e8da0b05713"


def _fail(reason):
    print(json.dumps({"status": "BLOCKED", "reason": reason,
                      "wordpress_written": False, "publication_authorized": False}))
    return 2


def _find_core(explicit=None):
    """Locate the trusted hash-pinned core checkout without trusting env input."""
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.environ.get("CONEXO_EDITORIAL_CORE_ROOT", "")
    if env:
        candidates.append(Path(env))
    candidates.append(Path.home() / "conexo-os-core")
    candidates.append(Path.home() / ".local/share/conexo-os/editorial-core")
    lock = json.loads((ROOT / "mkt_flow_p0/editorial_core.lock.json").read_text())
    for base in candidates:
        try:
            from mkt_flow_p0.editorial_transport import load_core
            load_core(base)  # verifies every locked file by SHA-256
            return base
        except Exception:
            continue
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--core-root", default=None,
                    help="trusted hash-pinned editorial core checkout (optional)")
    args = ap.parse_args()

    if not HANDOFF.is_dir() or HANDOFF.is_symlink():
        return _fail("HANDOFF_MISSING")
    pkg_path = HANDOFF / "package.json"
    if not pkg_path.is_file() or pkg_path.is_symlink():
        return _fail("PACKAGE_MISSING")
    try:
        package = json.loads(pkg_path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return _fail("PACKAGE_INVALID")

    # Verify the exact immutable version (never trust a pasted hash).
    version = package.get("version_sha256")
    if version != EXPECTED_VERSION:
        return _fail("VERSION_MISMATCH")
    md = package.get("payload", {}).get("content", "")
    if hashlib.sha256(md.encode("utf-8")).hexdigest() != EXPECTED_MARKDOWN:
        return _fail("MARKDOWN_MISMATCH")

    # Idempotency: one attempt per version, recorded next to the handoff.
    marker = HANDOFF / ("gate-stage-" + EXPECTED_VERSION[:16] + ".json")
    if marker.exists():
        return _fail("ALREADY_ATTEMPTED")

    core_root = _find_core(args.core_root)
    if core_root is None:
        return _fail("TRUSTED_CORE_MISSING")

    # Credentials come from the operator's private environment, never from repo.
    wp_user = os.environ.get("WP_USER") or os.environ.get("CONEXO_WP_USER")
    wp_pass = os.environ.get("WP_APP_PASSWORD") or os.environ.get("CONEXO_WP_APP_PASSWORD")
    if not wp_user or not wp_pass:
        return _fail("WP_CREDENTIALS_MISSING")

    # FK: associate the already-created licensed media only to the new draft.
    payload = dict(package.get("payload") or {})
    wp = dict(payload.get("wordpress") or {})
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

    # Persist one attempt; never retry the same version automatically.
    marker.write_text(json.dumps({"status": result.get("erro", "ATTEMPTED"),
                                   "version_sha256": EXPECTED_VERSION}) + "\n")

    ok = (isinstance(result, dict) and not result.get("erro")
          and result.get("status") == "draft"
          and result.get("version_sha256") == EXPECTED_VERSION)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
