#!/usr/bin/env bash
# Run the pipeline twice and diff row counts per relation. Empty diff = rerun-safe.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
bin/run.sh > /dev/null
bin/row-counts.sh > logs/counts-run1.tsv
bin/run.sh > /dev/null
bin/row-counts.sh > logs/counts-run2.tsv
echo "relation	run1	run2"
join -t "	" logs/counts-run1.tsv logs/counts-run2.tsv
echo
if diff logs/counts-run1.tsv logs/counts-run2.tsv; then
  echo "identical row counts across two consecutive runs"
else
  echo "row counts differ between runs" >&2
  exit 1
fi
