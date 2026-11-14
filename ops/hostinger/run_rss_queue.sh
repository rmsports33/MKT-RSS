#!/usr/bin/env bash
# Private Hostinger runner for the existing Python MKT-RSS queue-only intake.
# Not a deployment script. Fail-closed; no writes without explicit opt-in.
set -Eeuo pipefail
umask 077

die() { printf 'BLOCKED: %s\n' "$1" >&2; exit 2; }
[[ "${BASH_SOURCE[0]}" == "$0" ]] || die "execute, do not source"
[[ "${1:-}" == "--preflight" || "${1:-}" == "--run" ]] || die "usage: run_rss_queue.sh --preflight|--run"
MODE="$1"
[[ -n "${CONEXO_RUNNER_ROOT:-}" ]] || die "CONEXO_RUNNER_ROOT required"
[[ -d "$CONEXO_RUNNER_ROOT" ]] || die "runner directory not found"
ROOT="$(cd "$CONEXO_RUNNER_ROOT" && pwd -P)"
[[ -f "$ROOT/pipeline_rss.py" && -f "$ROOT/rss_queue_collect.py" ]] || die "MKT-RSS checkout incomplete"
case "$ROOT/" in
  */public_html/*|*/staging/*) die "runner must reside outside public_html/staging" ;;
esac

PYTHON="${CONEXO_PYTHON:-$ROOT/.venv/bin/python}"
[[ -x "$PYTHON" ]] || die "private Python missing"
"$PYTHON" -c 'import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] < (3,15) else 1)' \
  || die "requires Python 3.11-3.14 (Hostinger system Python 3.6 is not supported)"
"$PYTHON" -c 'import requests, feedparser, dotenv' \
  || die "private Python RSS dependencies missing"

# A consistent private config file prevents unexpected SQLite fallback.
CONFIG="${CONEXO_RSS_ENV_FILE:-$HOME/.config/conexo-os/rss-queue.env}"
[[ -f "$CONFIG" && ! -L "$CONFIG" ]] || die "private configuration missing or symlinked"
if [[ "$(stat -c '%a' "$CONFIG")" != 600 ]]; then
  die "private configuration must have mode 600"
fi
# Shellcheck disable: SC1090
set -a
source "$CONFIG"
set +a
[[ -n "${TURSO_DATABASE_URL:-}" && -n "${TURSO_AUTH_TOKEN:-}" ]] \
  || die "Turso secrets not configured; refusing SQLite fallback"
[[ "$TURSO_DATABASE_URL" =~ ^(libsql|https)://[A-Za-z0-9.-]+\.turso\.io/?$ ]] \
  || die "invalid Turso URL"
[[ "${CONEXO_RSS_TARGET_DB:-}" == "mkt-rss" ]] || die "explicit production target selection required"
[[ "$TURSO_DATABASE_URL" == *"mkt-rss-"* ]] || die "configured URL is not main mkt-rss"
[[ "$TURSO_DATABASE_URL" != *"homolog"* ]] || die "homolog DB not allowed as production target"
[[ "${CONEXO_PRODUCT_LINKS_ENABLED:-}" == "1" ]] || die "existing catalog link flag must be explicit"
[[ -z "${WP_APP_PASSWORD:-}" && -z "${WP_USER:-}" ]] \
  || die "WordPress credentials must not be present in this queue runner"
[[ -z "${GROQ_API_KEY:-}" ]] || die "LLM credentials not needed in queue-only mode"
export CONEXO_REQUIRE_CLOUD_PERSISTENCE=1
export CONEXO_RSS_SCHEMA_PREEXISTS=1
[[ "$MODE" == "--run" ]] || { printf 'PASS: private runner prerequisites and configuration checks; no network/write performed\n'; exit 0; }

[[ "${CONEXO_RSS_CRON_ACTIVE:-}" == "1" ]] || die "schedule not activated"
[[ "${CONEXO_RSS_WRITER_OWNER:-}" == "hostinger" ]] || die "Hostinger not elected as unique writer"
[[ "${CONEXO_ACTIONS_WRITER_DISABLED:-}" == "1" ]] \
  || die "proof of disabling GitHub Actions writer not acknowledged"

# In addition to the existing rss_queue_mutex lease in Turso, prevent local overlap.
LOCKDIR="${CONEXO_RSS_RUNTIME_DIR:-$HOME/.local/state/conexo-os}"
mkdir -p "$LOCKDIR"
chmod 700 "$LOCKDIR"
command -v flock >/dev/null || die "flock required for cron execution"
exec 9>"$LOCKDIR/rss-queue.lock"
flock -n 9 || die "local RSS writer already running"
cd "$ROOT"
LIMIT="${CONEXO_RSS_LIMIT:-2}"
[[ "$LIMIT" =~ ^[123]$ ]] || die "RSS limit must be 1, 2 or 3"
printf 'START rss-queue time_utc=%s mode=hostinger-only\n' "$(date -u +%FT%TZ)"
"$PYTHON" pipeline_rss.py --queue-only --fonte tecnoblog --limit "$LIMIT"
printf 'SUCCESS rss-queue time_utc=%s\n' "$(date -u +%FT%TZ)"
