#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
DB_PATH="$ROOT_DIR/data/app.db"

if [ ! -f "$DB_PATH" ]; then
  echo "Database not found at $DB_PATH" >&2
  exit 1
fi

# Escape single quotes for SQL literals
sql_escape() {
  local s="$1"
  s="${s//\'/''}"
  printf "%s" "$s"
}

run_sql_json() {
  local sql="$1"
  sqlite3 -json "$DB_PATH" "$sql"
}

