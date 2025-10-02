#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

if [ $# -lt 4 ]; then
  echo "Usage: $0 <lease_id> <amount_cents> <paid_at_ISO8601> <method> [reference]" >&2
  exit 1
fi

LEASE_ID="$1"
AMOUNT="$2"
PAID_AT_ESC=$(sql_escape "$3")
METHOD_ESC=$(sql_escape "$4")
REFERENCE_ESC=$(sql_escape "${5:-}")

SQL='
INSERT INTO payments (lease_id, amount_cents, paid_at, method, status, reference)
VALUES ('$LEASE_ID', '$AMOUNT', '\''$PAID_AT_ESC'\'', '\''$METHOD_ESC'\'', 'completed', '\''$REFERENCE_ESC'\'');
SELECT json_object("payment_id", last_insert_rowid());
'

eval "run_sql_json \"$SQL\""

