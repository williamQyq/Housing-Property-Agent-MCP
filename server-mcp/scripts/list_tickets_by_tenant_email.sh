#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <tenant_email> [status]" >&2
  exit 1
fi

EMAIL_ESC=$(sql_escape "$1")
STATUS=${2:-}
STATUS_ESC=$(sql_escape "$STATUS")

SQL='
SELECT json_group_array(json_object(
  "id", mt.id,
  "issue", mt.issue,
  "category", mt.category,
  "priority", mt.priority,
  "status", mt.status,
  "created_at", mt.created_at,
  "updated_at", mt.updated_at,
  "assigned_to", mt.assigned_to
))
FROM maintenance_tickets mt
JOIN leases l ON l.id = mt.lease_id
JOIN tenants t ON t.id = l.tenant_id
WHERE t.email = '\''$EMAIL_ESC'\''
  AND (''\''$STATUS_ESC'\'' = '' OR mt.status = '\''$STATUS_ESC'\'');
'

eval "run_sql_json \"$SQL\""

