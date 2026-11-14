#!/usr/bin/env python3
"""Stage an existing Unsplash image as a versioned, offline editorial image manifest.

Source/license externally checked 2026-11-14; crops visually reviewed in chat.
Not approval for publishing, not a property release, no WP/Groq/Turso access.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from PIL import Image
from mkt_flow_p0.image_protocol import validate_prepared_manifest

BASE = Path.home() / ".local/share/conexo-os/imagens/binance"
SOURCE = "https://unsplash.com/photos/a-rack-of-servers-in-a-server-room-2JJ3wBHu4_0"
IMAGE_URL = "https://images.unsplash.com/photo-1695668548342-c0c1ad479aee?auto=format&fit=crop&fm=jpg&q=85&w=1600"
EXPECTED = {
    "original": ("capa-original.jpg", (1600, 1067), "8d198de7610a04a808128f71d9e36d0031e5b367035356c182f2f68c64547d6d"),
    "desktop": ("capa-1440.jpg", (1440, 810), "b5ba5abd2bb4810eb3641d9c88a7e0d9108f401cb6a9567a44d8ce4f9e1d2d74"),
    "mobile": ("capa-390.jpg", (390, 219), "4a0a645f9b8ea33978acf769f2b6ea52bf13bda578f791df235518c874979917"),
}

def main():
    # A previous visual inspection is specific to these exact image digests.
    if not BASE.is_dir():
        raise SystemExit("BLOCKED: image directory missing")
    for label, (name, dims, digest) in EXPECTED.items():
        p = BASE / name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            raise SystemExit("BLOCKED: image integrity mismatch: " + label)
        with Image.open(p) as im:
            if im.format != "JPEG" or im.size != dims:
                raise SystemExit("BLOCKED: image dimensions mismatch: " + label)
    metadata = BASE / "metadata-imagem-binance.json"
    if not metadata.is_file():
        raise SystemExit("BLOCKED: original image metadata missing")
    m = json.loads(metadata.read_text(encoding="utf-8"))
    if (m.get("author") != "Kevin Ache"
        or m.get("source_page") != SOURCE
        or m.get("license_url") != "https://unsplash.com/license"
        or m.get("rights_review_status") != "PENDING_FINAL_CONFIRMATION"
        or m.get("visual_review_status") != "PENDING_MANUAL_CHECK"):
        raise SystemExit("BLOCKED: provenance metadata or original pending states differ")
    resource = {
        "id": "unsplash-kevin-ache-2JJ3wBHu4_0",
        "source_page": SOURCE,
        "image_url": IMAGE_URL,
        "author": "Kevin Ache",
        "license": "Unsplash License",
        "license_url": "https://unsplash.com/license",
        "checked_at": "2026-11-14",
        "alt": "Racks de servidores com cabos de rede em um centro de dados.",
        "caption": "Imagem ilustrativa de infraestrutura digital. Foto: Kevin Ache/Unsplash.",
        "credit": "Kevin Ache / Unsplash",
        "rights_review": "DOCUMENTED_SOURCE_CHECK",
        "content_fit_review": "PASS",
    }
    manifest = {
        "resource": resource,
        "visual_review": "ASSISTED_VISUAL_CHECK_COMPLETED",
        "content_fit_review": "PASS",
        "assets": {
            label: {"path": name, "width": dims[0], "height": dims[1], "sha256": digest}
            for label, (name, dims, digest) in EXPECTED.items() if label != "original"
        },
    }
    validate_prepared_manifest(manifest, base_dir=BASE)
    out = BASE / "image-manifest.json"
    if out.exists():
        existing = json.loads(out.read_text(encoding="utf-8"))
        if existing != manifest:
            raise SystemExit("BLOCKED: existing image manifest differs; manual reconciliation required")
    else:
        out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        os.chmod(out, 0o600)
    print(json.dumps({
        "status":"PREPARED_MANIFEST_VALIDATED",
        "manifest":str(out),
        "image_rights_documented":True,
        "editorial_publication_approved":False,
        "featured_media_id":None,
        "wordpress_written":False,
        "pending":["property_and_brand_rights_if_applicable","editorial_version_acceptance","wordpress_draft_readback"],
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
