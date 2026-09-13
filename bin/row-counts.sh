#!/usr/bin/env bash
# One line per relation: schema.name<TAB>rows<TAB>md5 of every row. Sorted, so two runs diff cleanly.
set -euo pipefail
cd "$(dirname "$0")/.."
DB="${1:-warehouse/gtm.duckdb}"
duckdb "$DB" -csv -noheader -c "
  select schema_name || '.' || table_name from duckdb_tables() where not internal
  union all
  select schema_name || '.' || view_name from duckdb_views() where not internal
  order by 1" | while read -r rel; do
  line=$(duckdb "$DB" -csv -noheader -separator '	' -c "select count(*), coalesce(md5(string_agg(t::varchar, chr(10) order by t::varchar)), '-') from $rel t")
  printf '%s\t%s\n' "$rel" "$line"
done
