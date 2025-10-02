#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

usage() {
  echo "Usage: $0 (--lease-id <id> | --tenant-email <email>) --issue <text> [--category <cat>] [--priority <p>] [--responsibility <r>] [--assigned-to <name>]" >&2
}

LEASE_ID=""; TENANT_EMAIL=""; ISSUE=""; CATEGORY=""; PRIORITY=""; RESPONSIBILITY=""; ASSIGNED_TO="";
while [ $# -gt 0 ]; do
  case "$1" in
    --lease-id) shift; LEASE_ID="$1" ;;
    --tenant-email) shift; TENANT_EMAIL="$1" ;;
    --issue) shift; ISSUE="$1" ;;
    --category) shift; CATEGORY="$1" ;;
    --priority) shift; PRIORITY="$1" ;;
    --responsibility) shift; RESPONSIBILITY="$1" ;;
    --assigned-to) shift; ASSIGNED_TO="$1" ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
  shift
done

if [ -z "$ISSUE" ]; then usage; exit 1; fi

if [ -z "$LEASE_ID" ]; then
  if [ -z "$TENANT_EMAIL" ]; then usage; exit 1; fi
  TEN_ESC=$(sql_escape "$TENANT_EMAIL")
  LEASE_ID=$(sqlite3 "$DB_PATH" "SELECT id FROM leases WHERE tenant_id=(SELECT id FROM tenants WHERE email='$TEN_ESC') ORDER BY start_date DESC LIMIT 1;")
fi

if [ -z "$LEASE_ID" ]; then echo "Could not resolve lease id" >&2; exit 1; fi

ISSUE_ESC=$(sql_escape "$ISSUE")
CATEGORY_ESC=$(sql_escape "$CATEGORY")
PRIORITY_ESC=$(sql_escape "$PRIORITY")
RESP_ESC=$(sql_escape "$RESPONSIBILITY")
ASSIGNED_ESC=$(sql_escape "$ASSIGNED_TO")
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)

SQL='
INSERT INTO maintenance_tickets (lease_id, issue, category, priority, status, responsibility, created_at, updated_at, assigned_to)
VALUES ('$LEASE_ID', '\''$ISSUE_ESC'\'', NULLIF('\''$CATEGORY_ESC'\'',''''), NULLIF('\''$PRIORITY_ESC'\'',''''), 'open', NULLIF('\''$RESP_ESC'\'',''''), '\''$NOW'\'', '\''$NOW'\'', NULLIF('\''$ASSIGNED_ESC'\'',''''));
SELECT json_object("ticket_id", last_insert_rowid());
'

eval "run_sql_json \"$SQL\""

