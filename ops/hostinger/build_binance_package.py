#!/usr/bin/env python3
"""Build the editorial-workflow/2 package for the reviewed Binance handoff.

This does NOT synthesize editorial judgment. It reuses the existing offline core
(editorial_core_offline.processar already produced the WordPress body) and the
canonical SEO handoff (vincular_seo_antes_da_revisao) to assemble the package the
Gate validator expects. Output is written into the private handoff dir so that
binance_gate_stage.py can find it. No network, no WordPress write, no approval.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HANDOFF = Path.home() / ".local/share/conexo-os/handoffs/binance-revisao-48f1ea5be313"
EXPECTED_VERSION = "d2ccb99e2dbe0dbc999a4b8e1fdd49d089c9299c679f5cb6200edc5db6e00fd2"
ARTICLE_REF = "binance-revisao-6e8da0b05713"


def _fail(reason):
    print(json.dumps({"status": "BLOCKED", "reason": reason,
                      "wordpress_written": False, "publication_authorized": False}))
    return 2


def main():
    if not HANDOFF.is_dir() or HANDOFF.is_symlink():
        return _fail("HANDOFF_MISSING")

    meta_path = HANDOFF / "article.metadata.json"
    md_path = HANDOFF / "article.md"
    report_path = HANDOFF / "binance-cobertura-roubo-cripto-2026-revisao.report.json"
    body_path = HANDOFF / "binance-cobertura-roubo-cripto-2026-revisao.wordpress-body.html"
    for p in (meta_path, md_path, report_path, body_path):
        if not p.is_file() or p.is_symlink():
            return _fail("HANDOFF_FILE_MISSING:" + p.name)

    try:
        article = json.loads(meta_path.read_text(encoding="utf-8"))
        report = json.loads(report_path.read_text(encoding="utf-8"))
        wordpress_body = body_path.read_text(encoding="utf-8")
    except (ValueError, OSError):
        return _fail("HANDOFF_PARSE_FAILED")

    slug = (article.get("seo") or {}).get("slug")
    if not isinstance(slug, str) or not slug:
        return _fail("SLUG_MISSING")

    # Assemble the unreviewed workflow/2 package from real handoff data.
    package = {
        "schema_version": "editorial-workflow/2",
        "stage": "draft",
        "payload": {
            "title": article.get("title"),
            "slug": slug,
            "content": wordpress_body,
            "sources": article.get("sources") or [],
            "article_id": article.get("article_id"),
            "genre": (article.get("editorial_brief") or {}).get("genre", "noticia"),
        },
    }

    # Bind advisory SEO from the already-generated manifest (no new judgment).
    try:
        from mkt_flow_p0.editorial_package_handoff import vincular_seo_antes_da_revisao
        package = vincular_seo_antes_da_revisao(package, report, wordpress_body)
    except Exception as exc:
        return _fail("SEO_BIND_FAILED:" + type(exc).__name__)

    # The workflow/2 package has its OWN version (digest of its payload), which
    # differs from the handoff digest (metadata+markdown). Both are recorded so
    # the stage script can bind the approved version to the exact package.
    version = package.get("version_sha256")
    if not isinstance(version, str) or len(version) != 64:
        return _fail("VERSION_INVALID")

    out = HANDOFF / "editorial-workflow-package.json"
    pointer = HANDOFF / "editorial-workflow-pointer.json"
    out.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pointer.write_text(json.dumps({
        "handoff_version_sha256": EXPECTED_VERSION,
        "package_version_sha256": version,
        "package_path": str(out),
        "built_from": "article.metadata.json + wordpress-body.html + report.json",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "PACKAGE_BUILT",
        "path": str(out),
        "pointer": str(pointer),
        "schema_version": package["schema_version"],
        "stage": package["stage"],
        "handoff_version_sha256": EXPECTED_VERSION,
        "package_version_sha256": version,
        "publication_authorized": False,
        "note": "Pacote montado de dados reais do handoff; versao propria; sem aprovacao/publicacao.",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
