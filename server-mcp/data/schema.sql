-- SQLite schema for Landlord–Tenant MCP Agent (MVP)
-- Tables: tenants, landlords, leases, rent_components, payments, maintenance_tickets

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tenants (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  phone TEXT
);

CREATE TABLE IF NOT EXISTS landlords (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  phone TEXT
);

CREATE TABLE IF NOT EXISTS leases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER NOT NULL,
  landlord_id INTEGER NOT NULL,
  unit TEXT NOT NULL,
  rent_amount INTEGER NOT NULL, -- amount in cents
  due_day INTEGER NOT NULL CHECK(due_day BETWEEN 1 AND 28),
  start_date TEXT NOT NULL, -- ISO8601
  end_date TEXT,            -- ISO8601
  notes TEXT,
  FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
  FOREIGN KEY (landlord_id) REFERENCES landlords(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rent_components (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lease_id INTEGER NOT NULL,
  label TEXT NOT NULL,
  amount_cents INTEGER NOT NULL DEFAULT 0,
  included INTEGER NOT NULL DEFAULT 1, -- 1=true, 0=false
  FOREIGN KEY (lease_id) REFERENCES leases(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lease_id INTEGER NOT NULL,
  amount_cents INTEGER NOT NULL,
  paid_at TEXT NOT NULL, -- ISO8601
  method TEXT,           -- e.g., bank_transfer, card, cash
  status TEXT NOT NULL DEFAULT 'completed', -- completed|pending|failed
  reference TEXT,
  FOREIGN KEY (lease_id) REFERENCES leases(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS maintenance_tickets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lease_id INTEGER NOT NULL,
  issue TEXT NOT NULL,
  category TEXT,
  priority TEXT DEFAULT 'medium', -- low|medium|high|urgent
  status TEXT DEFAULT 'open',     -- open|in-progress|resolved
  responsibility TEXT,            -- tenant|landlord|shared|unknown
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  assigned_to TEXT,
  FOREIGN KEY (lease_id) REFERENCES leases(id) ON DELETE CASCADE
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_leases_tenant ON leases(tenant_id);
CREATE INDEX IF NOT EXISTS idx_leases_landlord ON leases(landlord_id);
CREATE INDEX IF NOT EXISTS idx_payments_lease ON payments(lease_id);
CREATE INDEX IF NOT EXISTS idx_tickets_lease ON maintenance_tickets(lease_id);

