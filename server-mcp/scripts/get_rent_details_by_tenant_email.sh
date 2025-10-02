#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <tenant_email>" >&2
  exit 1
fi

EMAIL_ESC=$(sql_escape "$1")

SQL='
WITH lease AS (
  SELECT l.id, l.rent_amount, l.due_day, l.notes
  FROM leases l
  JOIN tenants t ON t.id = l.tenant_id
  WHERE t.email = '\''$EMAIL_ESC'\''
  ORDER BY l.start_date DESC LIMIT 1
)
SELECT json_object(
  "rent_amount", lease.rent_amount,
  "due_day", lease.due_day,
  "components", (
    SELECT json_group_array(json_object(
      "label", rc.label,
      "amount_cents", rc.amount_cents,
      "included", rc.included
    )) FROM rent_components rc WHERE rc.lease_id = lease.id
  ),
  "summary", (
    SELECT printf(
      'Base + included components; due on day %d%s', lease.due_day,
      CASE WHEN lease.notes IS NOT NULL AND lease.notes <> '' THEN ' — ' || lease.notes ELSE '' END
    )
  )
)
FROM lease;
'

eval "run_sql_json \"$SQL\""

