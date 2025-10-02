from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP as Server


server = Server("sqlite-mcp")


def db_path() -> Path:
  # .../server-mcp/Housing-Property-Agent-MCP/mcp_servers/mcp_sqlite_server.py
  # db at ../../data/app.db
  return Path(__file__).resolve().parents[1] / "data" / "app.db"


def get_conn() -> sqlite3.Connection:
  conn = sqlite3.connect(str(db_path()))
  conn.row_factory = sqlite3.Row
  return conn


@server.tool()
async def get_rent_details(lease_id: Optional[int] = None, tenant_email: Optional[str] = None) -> Dict[str, Any]:
  if lease_id is None and not tenant_email:
    raise ValueError("Provide lease_id or tenant_email")

  with get_conn() as conn:
    if lease_id is None:
      row = conn.execute(
        """
        SELECT l.id, l.rent_amount, l.due_day, l.notes
        FROM leases l
        JOIN tenants t ON t.id = l.tenant_id
        WHERE t.email = ?
        ORDER BY l.start_date DESC LIMIT 1
        """,
        (tenant_email,),
      ).fetchone()
    else:
      row = conn.execute(
        "SELECT id, rent_amount, due_day, notes FROM leases WHERE id = ?",
        (lease_id,),
      ).fetchone()
    if not row:
      return {}
    lease_id_val = int(row["id"])
    comps = [
      {
        "label": r["label"],
        "amount_cents": int(r["amount_cents"]),
        "included": bool(r["included"]),
      }
      for r in conn.execute("SELECT label, amount_cents, included FROM rent_components WHERE lease_id = ?", (lease_id_val,)).fetchall()
    ]
    notes = row["notes"] or ""
    summary = f"Base + included components; due on day {row['due_day']}" + (f" — {notes}" if notes else "")
    return {
      "rent_amount": int(row["rent_amount"]),
      "due_day": int(row["due_day"]),
      "components": comps,
      "summary": summary,
    }


@server.tool()
async def list_due_payments(reference_date: Optional[str] = None) -> List[Dict[str, Any]]:
  import datetime as dt

  ref = reference_date or dt.datetime.utcnow().strftime("%Y-%m-%d")
  with get_conn() as conn:
    out: List[Dict[str, Any]] = []
    for l in conn.execute("SELECT id, tenant_id, rent_amount, due_day FROM leases").fetchall():
      due_date = f"{ref[:7]}-{int(l['due_day']):02d}"
      last = conn.execute("SELECT MAX(date(paid_at)) AS d FROM payments WHERE lease_id=?", (int(l["id"]),)).fetchone()["d"]
      # status logic by month
      if last and last[:7] == ref[:7]:
        status = "paid"
      elif due_date <= ref:
        status = "overdue"
      else:
        status = "due"
      tenant_name = conn.execute("SELECT name FROM tenants WHERE id=?", (int(l["tenant_id"]),)).fetchone()["name"]
      out.append({
        "lease_id": int(l["id"]),
        "tenant": tenant_name,
        "amount_cents": int(l["rent_amount"]),
        "due_date": due_date,
        "status": status,
      })
    return out


@server.tool()
async def mark_payment_received(lease_id: int, amount_cents: int, paid_at: str, method: str, reference: Optional[str] = None) -> Dict[str, Any]:
  with get_conn() as conn:
    cur = conn.execute(
      """
      INSERT INTO payments (lease_id, amount_cents, paid_at, method, status, reference)
      VALUES (?, ?, ?, ?, 'completed', ?)
      """,
      (lease_id, amount_cents, paid_at, method, reference),
    )
    payment_id = cur.lastrowid
    conn.commit()
    return {"payment_id": int(payment_id)}


@server.tool()
async def create_maintenance_ticket(
  issue: str,
  lease_id: Optional[int] = None,
  tenant_email: Optional[str] = None,
  category: Optional[str] = None,
  priority: Optional[str] = None,
  responsibility_guess: Optional[str] = None,
  assigned_to: Optional[str] = None,
) -> Dict[str, Any]:
  if not lease_id and not tenant_email:
    raise ValueError("Provide lease_id or tenant_email")
  with get_conn() as conn:
    lease_id_val = lease_id
    if not lease_id_val:
      row = conn.execute(
        """
        SELECT l.id FROM leases l
        JOIN tenants t ON t.id = l.tenant_id
        WHERE t.email = ?
        ORDER BY l.start_date DESC LIMIT 1
        """,
        (tenant_email,),
      ).fetchone()
      if not row:
        raise ValueError("Could not resolve lease from tenant_email")
      lease_id_val = int(row["id"])
    import datetime as dt
    now = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    cur = conn.execute(
      """
      INSERT INTO maintenance_tickets (lease_id, issue, category, priority, status, responsibility, created_at, updated_at, assigned_to)
      VALUES (?, ?, NULLIF(?, ''), NULLIF(?, ''), 'open', NULLIF(?, ''), ?, ?, NULLIF(?, ''))
      """,
      (lease_id_val, issue, category or "", priority or "", responsibility_guess or "", now, now, assigned_to or ""),
    )
    ticket_id = cur.lastrowid
    conn.commit()
    return {"ticket_id": int(ticket_id)}


@server.tool()
async def list_tickets(
  lease_id: Optional[int] = None,
  tenant_email: Optional[str] = None,
  tenant_id: Optional[int] = None,
  status: Optional[str] = None,
) -> List[Dict[str, Any]]:
  if not lease_id and not tenant_email and not tenant_id:
    raise ValueError("Provide lease_id or tenant_email or tenant_id")
  with get_conn() as conn:
    lease_id_val = lease_id
    if not lease_id_val:
      row = None
      if tenant_email:
        row = conn.execute(
          """
          SELECT l.id FROM leases l
          JOIN tenants t ON t.id = l.tenant_id
          WHERE t.email = ?
          ORDER BY l.start_date DESC LIMIT 1
          """,
          (tenant_email,),
        ).fetchone()
      elif tenant_id:
        row = conn.execute(
          """
          SELECT l.id FROM leases l
          WHERE l.tenant_id = ?
          ORDER BY l.start_date DESC LIMIT 1
          """,
          (tenant_id,),
        ).fetchone()
      if not row:
        return []
      lease_id_val = int(row["id"])
    q = "SELECT id, issue, category, priority, status, created_at, updated_at, assigned_to FROM maintenance_tickets WHERE lease_id = ?"
    params: List[Any] = [lease_id_val]
    if status:
      q += " AND status = ?"
      params.append(status)
    rows = conn.execute(q, tuple(params)).fetchall()
    return [
      {k: r[k] for k in r.keys()}
      | {"id": int(r["id"])}
      for r in rows
    ]


@server.tool()
async def list_all_tickets(limit: Optional[int] = None) -> List[Dict[str, Any]]:
  """List recent maintenance tickets with tenant name and lease unit."""
  with get_conn() as conn:
    q = (
      """
      SELECT mt.id, mt.issue, mt.category, mt.priority, mt.status,
             mt.created_at, mt.updated_at, mt.assigned_to,
             t.name AS tenant, l.unit AS lease_unit
      FROM maintenance_tickets mt
      JOIN leases l ON l.id = mt.lease_id
      JOIN tenants t ON t.id = l.tenant_id
      ORDER BY datetime(mt.created_at) DESC
      """
    )
    if limit and limit > 0:
      q += " LIMIT ?"
      rows = conn.execute(q, (int(limit),)).fetchall()
    else:
      rows = conn.execute(q).fetchall()
    out: List[Dict[str, Any]] = []
    for r in rows:
      item = {k: r[k] for k in r.keys()}
      item["id"] = int(r["id"])  # normalize id to int
      out.append(item)
    return out


async def main() -> None:
  await server.run_stdio_async()


if __name__ == "__main__":
  import asyncio
  asyncio.run(main())
