#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REF_DATE=${1:-}
if [ -z "$REF_DATE" ]; then
  # Use today in UTC
  REF_DATE=$(date -u +%Y-%m-%d)
fi

SQL='
WITH months AS (
  SELECT l.id AS lease_id, l.due_day,
         date(substr("'$REF_DATE'",1,7) || '-' || printf('%02d', l.due_day)) AS due_date
  FROM leases l
), latest_pay AS (
  SELECT p.lease_id, MAX(date(p.paid_at)) AS last_paid_date
  FROM payments p GROUP BY p.lease_id
)
SELECT json_group_array(json_object(
  "lease_id", m.lease_id,
  "tenant", (SELECT name FROM tenants t JOIN leases l ON l.tenant_id=t.id WHERE l.id=m.lease_id),
  "amount_cents", (SELECT rent_amount FROM leases WHERE id=m.lease_id),
  "due_date", m.due_date,
  "status", CASE
    WHEN date(m.due_date) <= date("'$REF_DATE'") AND (
      lp.last_paid_date IS NULL OR strftime('%Y-%m', lp.last_paid_date) < strftime('%Y-%m', m.due_date)
    ) THEN 'overdue'
    WHEN (
      lp.last_paid_date IS NOT NULL AND strftime('%Y-%m', lp.last_paid_date) = strftime('%Y-%m', m.due_date)
    ) THEN 'paid'
    ELSE 'due'
  END
))
FROM months m
LEFT JOIN latest_pay lp ON lp.lease_id = m.lease_id;
'

eval "run_sql_json \"$SQL\""

