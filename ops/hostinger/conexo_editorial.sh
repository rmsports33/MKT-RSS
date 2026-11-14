#!/usr/bin/env bash
# Explicit one-shot editorial work on the existing Hostinger checkout.
# No schedule, no WordPress writes, no publication. RSS/Turso queue remains isolated.
set -Eeuo pipefail
umask 077
ROOT="$HOME/mkt-rss-runner"
PY="$ROOT/.venv/bin/python"
HANDOFF_DIR="$HOME/.local/share/conexo-os/handoffs"
GROQ_TOKEN="$HOME/.config/conexo-os/groq-editorial.token"
[[ -x "$PY" && -f "$ROOT/pipeline_rss.py" ]] || { echo "BLOCKED: editorial checkout/venv unavailable"; exit 2; }
cd "$ROOT"

case "${1:-}" in
  --inspect)
    "$PY" - "$HANDOFF_DIR" <<'PY'
import json, sys
from pathlib import Path
base = Path(sys.argv[1])
files = sorted(base.glob('rss_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
if not files:
    print("BLOCKED: no saved editorial package")
    sys.exit(2)
p=files[0]
d=json.loads(p.read_text(encoding='utf-8'))
m=d.get("metadata", {})
body=d.get("markdown", "")
sources=m.get("sources", [])
claims=m.get("claims", [])
print(json.dumps({
    "file":p.name, "title":m.get("title"), "status":d.get("review_status"),
    "words":len(body.split()), "sources":len(sources), "claims":len(claims),
    "version_sha256_present":bool(d.get("version_sha256")),
    "wordpress_written":d.get("wordpress_written"),
    "needs": [need for need, pending in [
      ("substantive_review", not m.get("review",{}).get("approved")),
      ("multisource_research", len(sources)<2),
      ("evidence_mapping", not claims),
      ("image_license_and_desktop_mobile_review", True),
      ("human_approval", True)
    ] if pending]
}, ensure_ascii=False, indent=2, default=str))
PY
    ;;
  --show-article)
    # Read the saved article only; do not expose credentials, private env or trace files.
    "$PY" - "$HANDOFF_DIR" <<'PY'
import json, sys
from pathlib import Path
base = Path(sys.argv[1])
files = sorted(base.glob('rss_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
if not files:
    print("BLOCKED: no saved editorial package")
    sys.exit(2)
d = json.loads(files[0].read_text(encoding='utf-8'))
markdown = d.get('markdown')
if not isinstance(markdown, str) or not markdown.strip() or len(markdown) > 100000:
    print("BLOCKED: article missing or too large")
    sys.exit(2)
print("=== ARTIGO PARA REVISAO (NAO APROVADO) ===")
print(markdown)
PY
    ;;
  --image-stage)
    # Verified Unsplash provenance and chat-reviewed crop -> private immutable manifest.
    # Not WordPress, publication or a human approval.
    unset WP_USER WP_APP_PASSWORD CONEXO_WP_USER CONEXO_WP_APP_PASSWORD
    unset TURSO_AUTH_TOKEN GROQ_API_KEY CONEXO_RSS_DRAFT CONEXO_RSS_DRAFT_STAGING
    unset CONEXO_GATE_REMEDIATION_AUTO
    "$PY" ops/hostinger/prepare_binance_visual_manifest.py
    ;;
  --import-binance-reviewed)
    # Fresh immutable private package with the exact-SHA assistant critique and image.
    unset WP_USER WP_APP_PASSWORD CONEXO_WP_USER CONEXO_WP_APP_PASSWORD
    unset TURSO_AUTH_TOKEN GROQ_API_KEY CONEXO_RSS_DRAFT CONEXO_RSS_DRAFT_STAGING
    unset CONEXO_GATE_REMEDIATION_AUTO
    "$PY" ops/hostinger/import_binance_revision.py --with-image --editorial-review
    ;;
  --import-binance-image)
    # New reviewed version with licensed assets and HTML preview. Remains pending human acceptance.
    unset WP_USER WP_APP_PASSWORD CONEXO_WP_USER CONEXO_WP_APP_PASSWORD
    unset TURSO_AUTH_TOKEN GROQ_API_KEY CONEXO_RSS_DRAFT CONEXO_RSS_DRAFT_STAGING
    unset CONEXO_GATE_REMEDIATION_AUTO
    "$PY" ops/hostinger/import_binance_revision.py --with-image
    ;;
  --image-check)
    # One-shot local QA + contact sheet. No approval or WordPress changes.
    unset WP_USER WP_APP_PASSWORD CONEXO_WP_USER CONEXO_WP_APP_PASSWORD
    unset TURSO_AUTH_TOKEN GROQ_API_KEY CONEXO_RSS_DRAFT CONEXO_RSS_DRAFT_STAGING
    unset CONEXO_GATE_REMEDIATION_AUTO
    "$PY" ops/hostinger/verify_binance_image.py
    ;;
  --import-binance)
    # Imports the GitHub-reviewed Markdown as a distinct private, pending package.
    # Never calls Groq, Turso, WordPress or the Gate write endpoints.
    unset WP_USER WP_APP_PASSWORD CONEXO_WP_USER CONEXO_WP_APP_PASSWORD
    unset TURSO_AUTH_TOKEN GROQ_API_KEY CONEXO_RSS_DRAFT CONEXO_RSS_DRAFT_STAGING
    unset CONEXO_GATE_REMEDIATION_AUTO
    "$PY" ops/hostinger/import_binance_revision.py
    ;;
  --handoff-one)
    [[ -s "$GROQ_TOKEN" && ! -L "$GROQ_TOKEN" ]] || { echo "BLOCKED: private Groq credential missing"; exit 2; }
    [[ "$(stat -c '%a' "$GROQ_TOKEN")" == 600 ]] || { echo "BLOCKED: credential permissions"; exit 2; }
    mkdir -p "$HANDOFF_DIR"
    # No WordPress or Turso credentials in this process.
    unset WP_APP_PASSWORD WP_USER CONEXO_WP_APP_PASSWORD CONEXO_WP_USER TURSO_AUTH_TOKEN
    unset CONEXO_RSS_DRAFT CONEXO_RSS_DRAFT_STAGING CONEXO_GATE_REMEDIATION_AUTO
    export GROQ_API_KEY="$(cat "$GROQ_TOKEN")"
    export GROQ_MODEL="openai/gpt-oss-120b"
    "$PY" pipeline_rss.py --fonte tecnoblog --limit 1 --handoff-only --handoff-dir "$HANDOFF_DIR"
    ;;
  *)
    echo "Usage: bash ops/hostinger/conexo_editorial.sh --inspect|--show-article|--image-check|--image-stage|--import-binance-reviewed|--import-binance-image|--import-binance|--handoff-one"
    exit 2
    ;;
esac
