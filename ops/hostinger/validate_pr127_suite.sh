#!/usr/bin/env bash
# One-shot, isolated PR #127 test runner for the existing Hostinger Python venv.
# Worktree is outside public_html; tests are offline and never call WordPress writes.
set -uo pipefail

ROOT="$HOME/mkt-rss-runner"
WORK="$HOME/tmp/p127"
LOCK="$HOME/tmp/p127-v2.lock"
PR_REF="fix/editorial-import-provenance-video-20261118"
PYTHON="$ROOT/.venv/bin/python"

mkdir -p "$HOME/tmp"
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "VALIDATION_ALREADY_RUNNING"
  exit 0
fi

cleanup() {
  cd "$ROOT" 2>/dev/null || true
  git worktree remove --force "$WORK" >/dev/null 2>&1 || true
  rmdir "$LOCK" >/dev/null 2>&1 || true
}
trap cleanup EXIT

if [ ! -x "$PYTHON" ]; then
  echo "HOSTINGER_PYTHON_NOT_FOUND=$PYTHON"
  exit 4
fi

if ! git -C "$ROOT" fetch --quiet origin "$PR_REF"; then
  echo "PR127_FETCH_FAILED"
  exit 5
fi
REMOTE_HEAD="$(git -C "$ROOT" rev-parse FETCH_HEAD)"
if ! git -C "$WORK" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "WORKTREE_NOT_FOUND=$WORK"
  exit 6
fi
WORK_HEAD="$(git -C "$WORK" rev-parse HEAD)"
echo "PR127_REMOTE_HEAD=$REMOTE_HEAD"
echo "PR127_WORKTREE_HEAD=$WORK_HEAD"
if [ "$WORK_HEAD" != "$REMOTE_HEAD" ]; then
  echo "WORKTREE_HEAD_MISMATCH_RECREATE_FROM_FETCH_HEAD"
  exit 7
fi

PYTHON_VERSION="$("$PYTHON" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
echo "HOSTINGER_PYTHON_VERSION=$PYTHON_VERSION"
case "$PYTHON_VERSION" in
  3.11.*) ;;
  *) echo "PYTHON_VERSION_MISMATCH_EXPECTED_3.11"; exit 8 ;;
esac

cd "$WORK" || { echo "WORKTREE_NOT_FOUND"; exit 6; }
if "$PYTHON" -m pytest -q \
  tests/test_editorial_provenance.py \
  tests/test_editorial_publish_gate.py \
  tests/test_editorial_import_video_provenance.py \
  tests/test_editorial_video.py \
  tests/test_editorial_video_formatos.py \
  tests/test_imported_editorial_flow.py \
  tests/test_editorial_wordpress_adapter.py \
  tests/test_validate_wordpress_snapshot.py
then
  RESULT=0
else
  RESULT=$?
fi
echo "PR127_TEST_EXIT=$RESULT"
exit "$RESULT"
