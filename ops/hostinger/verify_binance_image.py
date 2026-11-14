#!/usr/bin/env python3
"""Offline visual QA for a previously downloaded image. Never approves image rights.

Produces a technical report and a side-by-side contact sheet, without touching
the editorial handoff or WordPress. No network, Groq, image-generation or API.
"""
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps, ImageStat

BASE = Path.home() / ".local/share/conexo-os/imagens/binance"
META = BASE / "metadata-imagem-binance.json"
FILES = {
    "original": ("capa-original.jpg", (1600, 1067),
                 "8d198de7610a04a808128f71d9e36d0031e5b367035356c182f2f68c64547d6d"),
    "desktop_1440": ("capa-1440.jpg", (1440, 810),
                     "b5ba5abd2bb4810eb3641d9c88a7e0d9108f401cb6a9567a44d8ce4f9e1d2d74"),
    "mobile_390": ("capa-390.jpg", (390, 219),
                   "4a0a645f9b8ea33978acf769f2b6ea52bf13bda578f791df235518c874979917"),
}
SOURCE_PAGE = "https://unsplash.com/photos/a-rack-of-servers-in-a-server-room-2JJ3wBHu4_0"
LICENSE = "https://unsplash.com/license"
AUTHOR = "Kevin Ache"


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(131072), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main():
    BASE.mkdir(parents=True, exist_ok=True, mode=0o700)
    checks = {}
    images = {}
    for role, (name, expected_size, expected_hash) in FILES.items():
        path = BASE / name
        record = {"path": name, "exists": path.is_file()}
        if path.is_file():
            record["sha256"] = digest(path)
            record["sha256_matches_baseline"] = record["sha256"] == expected_hash
            try:
                with Image.open(path) as im:
                    im.verify()
                with Image.open(path) as im:
                    record["size"] = list(im.size)
                    record["format"] = im.format
                    record["correct_dimensions"] = im.size == expected_size
                    record["jpeg_valid"] = im.format == "JPEG"
                    if record["jpeg_valid"]:
                        images[role] = ImageOps.exif_transpose(im).convert("RGB")
            except (OSError, ValueError) as exc:
                record["image_error"] = type(exc).__name__
        checks[role] = record

    meta = {}
    if META.is_file():
        try:
            meta = json.loads(META.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError):
            meta = {}
    metadata_consistent = (
        meta.get("source_page") == SOURCE_PAGE
        and meta.get("author") == AUTHOR
        and meta.get("license_url") == LICENSE
        and meta.get("visual_review_status") == "PENDING_MANUAL_CHECK"
        and meta.get("rights_review_status") == "PENDING_FINAL_CONFIRMATION"
        and all(meta.get("files", {}).get(role, {}).get("sha256") == expected[2]
                for role, expected in FILES.items())
    )

    checks_ok = all(
        x.get("exists") and x.get("sha256_matches_baseline")
        and x.get("correct_dimensions") and x.get("jpeg_valid")
        for x in checks.values()
    )

    sheet_file = None
    if checks_ok:
        sheet = Image.new("RGB", (1520, 1180), "#eeeeee")
        draw = ImageDraw.Draw(sheet)
        draw.text((40, 12), "BINANCE - REVISÃO DE CAPA / IMAGEM ILUSTRATIVA", fill="#111111")
        draw.text((40, 36), "DESKTOP 1440 x 810", fill="#111111")
        sheet.paste(images["desktop_1440"], (40, 58))
        draw.text((40, 884), "MOBILE 390 x 219 (ampliado apenas para visualização)", fill="#111111")
        mobile = images["mobile_390"].resize((468, 263), Image.Resampling.NEAREST)
        sheet.paste(mobile, (40, 909))
        sheet_file = "conferencia-visual-binance.jpg"
        sheet.save(BASE / sheet_file, "JPEG", quality=90)
        os.chmod(BASE / sheet_file, 0o600)

    result = {
        "schema": "conexo-image-technical-qa/1",
        "article_ref": meta.get("article_ref", "binance-revisao-6e8da0b05713"),
        "files": checks,
        "technical_checks": "PASS" if checks_ok else "FAIL",
        "metadata_consistent": metadata_consistent,
        "contact_sheet": str(BASE / sheet_file) if sheet_file else None,
        "rights_review": "PENDING_HUMAN_REVIEW",
        "visual_review": "PENDING_HUMAN_REVIEW",
        "content_fit_review": "PENDING_HUMAN_REVIEW",
        "wordpress_written": False,
        "publication_authorized": False,
        "notes": [
            "Technical checks cannot establish subject appropriateness or license clearance.",
            "Unsplash License is not currently accepted by image_protocol.LICENSES for automatic manifest promotion.",
            "Do not set ASSISTED_VISUAL_CHECK_COMPLETED or PASS without actually inspecting both crops.",
            "The current handoff remains unchanged and awaiting human editorial approval.",
        ],
    }
    report = BASE / "relatorio-imagem-binance.json"
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(report, 0o600)
    print(json.dumps({
        "technical_checks": result["technical_checks"],
        "metadata_consistent": metadata_consistent,
        "visual_review": result["visual_review"],
        "rights_review": result["rights_review"],
        "contact_sheet": result["contact_sheet"],
        "report": str(report),
        "wordpress_written": False,
        "publication_authorized": False,
    }, ensure_ascii=False, indent=2))
    return 0 if checks_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
