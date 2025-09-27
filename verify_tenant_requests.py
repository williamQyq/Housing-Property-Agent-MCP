#!/usr/bin/env python3
"""
Verify that the TenantPortal data source (GET /tenant/requests?leaseId=1)
returns all rows from the maintenance_tickets table in app.db for lease_id=1.

Usage:
  1) Ensure the Master Server is running (e.g., via `bash start_demo.sh`).
  2) Run: python3 verify_tenant_requests.py
  3) Optionally set MASTER_BASE env var (default: http://localhost:8000)

This script compares:
  - DB rows: server-mcp/Housing-Property-Agent-MCP/data/app.db
  - HTTP:   {MASTER_BASE}/tenant/requests?leaseId=1&limit=1000

It asserts that every DB ticket appears in the API response with the expected
mapping used by the frontend (id, description, urgency, category, status, date).
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlencode
from urllib.request import urlopen, Request


DB_PATH = Path("server-mcp/Housing-Property-Agent-MCP/data/app.db")
MASTER_BASE = os.environ.get("MASTER_BASE", "http://localhost:8000").rstrip("/")


@dataclass
class DbTicket:
    id: int
    issue: str
    priority: str
    category: str
    status: str
    created_at: str


def load_db_tickets(lease_id: int = 1) -> List[DbTicket]:
    if not DB_PATH.exists():
        raise SystemExit(f"DB not found at {DB_PATH}. Initialize the DB before running this test.")
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    try:
        cur = con.execute(
            """
            SELECT id, issue, priority, category, status, created_at
            FROM maintenance_tickets
            WHERE lease_id = ?
            ORDER BY id ASC
            """,
            (lease_id,),
        )
        rows = [DbTicket(**dict(r)) for r in cur.fetchall()]
        return rows
    finally:
        con.close()


def load_api_items(lease_id: int = 1, limit: int = 1000) -> List[Dict]:
    qs = urlencode({"leaseId": lease_id, "limit": limit})
    url = f"{MASTER_BASE}/tenant/requests?{qs}"
    try:
        with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            items = payload.get("items") or []
            if not isinstance(items, list):
                raise ValueError("Invalid response: 'items' is not a list")
            return items
    except Exception as e:
        raise SystemExit(f"Failed to fetch {url}: {e}")


def verify_mapping(db_rows: List[DbTicket], api_items: List[Dict]) -> None:
    # Build index by API id (e.g., REQ{id}) and by description for robustness
    api_by_id = {str(item.get("id")):
                 item for item in api_items}

    errors: List[str] = []

    # Count check
    if len(api_items) != len(db_rows):
        errors.append(
            f"Count mismatch: API returned {len(api_items)} items but DB has {len(db_rows)} tickets for lease_id=1"
        )

    # Field-level checks
    for r in db_rows:
        api_id = f"REQ{r.id}"
        item = api_by_id.get(api_id)
        if not item:
            errors.append(f"Missing ticket in API: expected id={api_id} (DB id={r.id})")
            continue
        # Description
        if (item.get("description") or "").strip() != (r.issue or "").strip():
            errors.append(f"Description mismatch for {api_id}: API='{item.get('description')}' DB='{r.issue}'")
        # Category
        if (item.get("category") or "").strip() != (r.category or "").strip():
            errors.append(f"Category mismatch for {api_id}: API='{item.get('category')}' DB='{r.category}'")
        # Urgency (priority)
        api_urg = (item.get("urgency") or "").strip().lower()
        db_pri = (r.priority or "").strip().lower()
        if api_urg != db_pri:
            errors.append(f"Urgency/priority mismatch for {api_id}: API='{api_urg}' DB='{db_pri}'")
        # Status
        api_status = (item.get("status") or "").strip().lower().replace("_", "-")
        db_status = (r.status or "").strip().lower().replace("_", "-")
        if api_status != db_status:
            errors.append(f"Status mismatch for {api_id}: API='{api_status}' DB='{db_status}'")
        # Date (YYYY-MM-DD)
        api_date = (item.get("date") or "").strip()[:10]
        db_date = (r.created_at or "").strip()[:10]
        if api_date != db_date:
            errors.append(f"Date mismatch for {api_id}: API='{api_date}' DB='{db_date}'")

    if errors:
        print("\n❌ Verification failed:")
        for e in errors:
            print(" -", e)
        raise SystemExit(1)
    else:
        print(
            f"\n✅ Verification passed: {len(api_items)} API items match {len(db_rows)} DB tickets for lease_id=1."
        )


def main() -> None:
    print("🔎 Loading DB tickets for lease_id=1…")
    db_rows = load_db_tickets(lease_id=1)
    print(f"   DB rows: {len(db_rows)}")
    print("🌐 Fetching API items from /tenant/requests?leaseId=1&limit=1000…")
    api_items = load_api_items(lease_id=1, limit=1000)
    print(f"   API items: {len(api_items)}")
    verify_mapping(db_rows, api_items)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        sys.exit(e.code)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

