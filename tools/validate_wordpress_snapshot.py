"""Validate a previously captured WordPress edit/view snapshot offline.

The capture itself may come from an authenticated GET, but replay and validation
need no WordPress credentials, network access, or write capability.

Input JSON:
{
  "edit_post": { ... response from context=edit ... },
  "view_post": { ... response from context=view ... }
}

Only a metadata/hash summary is printed; editorial content is never emitted.
"""
import argparse
import hashlib
import json
from pathlib import Path

from editorial_wordpress_adapter import (
    assemble_wordpress_context_readback,
    validate_wordpress_content_readback,
)


def validate_snapshot(snapshot):
    if not isinstance(snapshot, dict):
        return {"valid": False, "blockers": ["snapshot_invalid"]}
    edit_post = snapshot.get("edit_post")
    view_post = snapshot.get("view_post")
    combined, blockers = assemble_wordpress_context_readback(edit_post, view_post)
    if blockers:
        return {"valid": False, "blockers": blockers}
    result = validate_wordpress_content_readback(combined)
    raw = combined["content"]["raw"]
    rendered = combined["content"]["rendered"]
    return {
        "valid": result["valid"],
        "blockers": result["blockers"],
        "post_id": combined["id"],
        "status": combined["status"],
        "modified": combined["modified"],
        "raw_chars": len(raw),
        "rendered_chars": len(rendered),
        "raw_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "rendered_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        "video_ids": result["video_ids"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate a saved WordPress edit/view snapshot without network access."
    )
    parser.add_argument("snapshot", help="Path to a JSON file containing edit_post and view_post")
    args = parser.parse_args()
    try:
        snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
        result = validate_snapshot(snapshot)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        result = {"valid": False, "blockers": ["snapshot_unreadable_or_invalid_json"]}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["valid"] else 2)


if __name__ == "__main__":
    main()
