#!/bin/bash
# Cron entrypoint for the MKT-RSS remote controller (Hostinger).
#
# Why this wrapper exists: the hPanel "Command to execute" field has a
# 255-character limit, and the previous long inline command (with `{ ...; }`,
# `||` and `&&`) was not executed by the scheduler. The scheduler now calls
# this short, versioned script instead.
#
# This script never publishes, never writes WordPress and never acts on its
# own: the controller still requires an explicit request published on the
# trusted GitHub branch, validates it against a strict allowlist, and writes
# a durable receipt per job_id.
set -u

ROOT="${MKT_RSS_RUNNER_ROOT:-$HOME/mkt-rss-runner}"
cd "$ROOT" || { echo "BLOCKED: runner root missing"; exit 1; }

# Keep the trusted checkout current only when the working tree is clean.
# A failed update is not fatal and never changes how the controller runs.
if [ -z "$(git status --porcelain 2>/dev/null)" ]; then
  git pull --ff-only origin feat/hostinger-runtime-independente-20261113 >/dev/null 2>&1 || true
fi

exec .venv/bin/python ops/hostinger/remote_controller.py
