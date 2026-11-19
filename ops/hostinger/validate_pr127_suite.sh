#!/usr/bin/env bash
# One-shot, isolated PR #127 test runner for the existing Hostinger Python venv.
# Worktree is outside public_html; tests are offline and never call WordPress writes.
set -u
ROOT="$HOME/mkt-rss-runner"
WORK="$HOME/tmp/mkt-rss-pr127-validation-20261119"
LOCK="$HOME/tmp/mkt-rss-pr127-validation-20261119.lock"
mkdir -p "$HOME/tmp"
if [ -e "$LOCK" ]; then
  echo "VALIDATION_ALREADY_STARTED"
  exit 0
fi
: > "$LOCK"
cleanup() {
  cd "$ROOT" 2>/dev/null || true
  git worktree remove --force "$WORK" >/dev/null 2>&1 || true
}
trap cleanup EXIT
cd "$WORK" || { echo "WORKTREE_NOT_FOUND"; exit 4; }
"$ROOT/.venv/bin/python" -m pytest -q \
  tests/test_editorial_provenance.py \
  tests/test_editorial_publish_gate.py \
  tests/test_editorial_import_video_provenance.py \
  tests/test_editorial_video.py \
  tests/test_editorial_video_formatos.py \
  tests/test_imported_editorial_flow.py \
  tests/test_editorial_wordpress_adapter.py \
  tests/test_validate_wordpress_snapshot.py
RESULT=$?
echo "PR127_TEST_EXIT=$RESULT"
exit "$RESULT"
