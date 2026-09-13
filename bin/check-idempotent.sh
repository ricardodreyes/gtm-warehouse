#!/usr/bin/env bash
# Run the pipeline twice over the same source files and diff row count and content hash per relation.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
bin/run.sh > /dev/null
bin/row-counts.sh > logs/counts-run1.tsv
bin/run.sh > /dev/null
bin/row-counts.sh > logs/counts-run2.tsv
echo "relation	rows	md5(run1)	rows	md5(run2)"
join -t "	" logs/counts-run1.tsv logs/counts-run2.tsv
echo
if diff logs/counts-run1.tsv logs/counts-run2.tsv; then
  echo "identical row counts and content hashes across two consecutive runs"
else
  echo "row counts or content differ between runs" >&2
  exit 1
fi
