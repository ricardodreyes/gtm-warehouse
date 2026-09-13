#!/usr/bin/env bash
# Snapshot the raw sources into raw/<date>/, point raw/latest at it, run dbt build, log everything.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="/opt/homebrew/bin:$HOME/.local/bin:$PATH"

SRC="${GTM_RAW_SRC:-$HOME/signet/outreach/app-leads}"
DAY="$(date +%F)"
LOG="logs/run-$(date +%F-%H%M%S).log"
mkdir -p "raw/$DAY" logs

for f in merged.json verify-input.csv sent.txt replies.txt; do
  cp "$SRC/$f" "raw/$DAY/$f"
done
ln -sfn "$DAY" raw/latest

{
  echo "run started $(date -Iseconds) raw=$DAY"
  uv run dbt build --no-use-colors
  echo "run finished $(date -Iseconds)"
} 2>&1 | tee "$LOG"
exit "${PIPESTATUS[0]}"
