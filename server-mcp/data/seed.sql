-- Seed data for demo/testing

BEGIN TRANSACTION;

INSERT INTO tenants (name, email, phone) VALUES
  ('Sarah Johnson', 'sarah@example.com', '+1-555-0101'),
  ('Mike Chen', 'mike@example.com', '+1-555-0102');

INSERT INTO landlords (name, email, phone) VALUES
  ('Acme Property Mgmt', 'landlord@example.com', '+1-555-1000');

-- Lease for Sarah
INSERT INTO leases (tenant_id, landlord_id, unit, rent_amount, due_day, start_date, end_date, notes)
VALUES ((SELECT id FROM tenants WHERE email='sarah@example.com'),
        (SELECT id FROM landlords WHERE email='landlord@example.com'),
        'Unit 2A', 220000, 5, '2024-01-01', NULL,
        'Late fee: $50 after 3-day grace period');

-- Lease for Mike
INSERT INTO leases (tenant_id, landlord_id, unit, rent_amount, due_day, start_date, end_date, notes)
VALUES ((SELECT id FROM tenants WHERE email='mike@example.com'),
        (SELECT id FROM landlords WHERE email='landlord@example.com'),
        'Unit 3B', 200000, 1, '2024-01-01', NULL,
        'No grace period; daily penalty $10 after due date');

-- Rent components for Sarah (Unit 2A)
INSERT INTO rent_components (lease_id, label, amount_cents, included)
SELECT l.id, 'Base Rent', 200000, 1 FROM leases l WHERE l.unit='Unit 2A';
INSERT INTO rent_components (lease_id, label, amount_cents, included)
SELECT l.id, 'Water', 0, 1 FROM leases l WHERE l.unit='Unit 2A';
INSERT INTO rent_components (lease_id, label, amount_cents, included)
SELECT l.id, 'Trash', 0, 1 FROM leases l WHERE l.unit='Unit 2A';
INSERT INTO rent_components (lease_id, label, amount_cents, included)
SELECT l.id, 'Parking', 20000, 0 FROM leases l WHERE l.unit='Unit 2A';

-- Rent components for Mike (Unit 3B)
INSERT INTO rent_components (lease_id, label, amount_cents, included)
SELECT l.id, 'Base Rent', 180000, 1 FROM leases l WHERE l.unit='Unit 3B';
INSERT INTO rent_components (lease_id, label, amount_cents, included)
SELECT l.id, 'Internet', 0, 0 FROM leases l WHERE l.unit='Unit 3B';

-- Payments history
INSERT INTO payments (lease_id, amount_cents, paid_at, method, status, reference)
SELECT l.id, 220000, '2024-08-05T10:00:00Z', 'bank_transfer', 'completed', 'AUG-2024-0001'
FROM leases l WHERE l.unit='Unit 2A';
INSERT INTO payments (lease_id, amount_cents, paid_at, method, status, reference)
SELECT l.id, 220000, '2024-09-06T09:30:00Z', 'bank_transfer', 'completed', 'SEP-2024-0002'
FROM leases l WHERE l.unit='Unit 2A';

INSERT INTO payments (lease_id, amount_cents, paid_at, method, status, reference)
SELECT l.id, 200000, '2024-08-01T12:00:00Z', 'card', 'completed', 'AUG-2024-0101'
FROM leases l WHERE l.unit='Unit 3B';

-- Open maintenance ticket example
INSERT INTO maintenance_tickets (
  lease_id, issue, category, priority, status, responsibility, created_at, updated_at, assigned_to
) SELECT l.id, 'Leaking faucet in kitchen', 'plumbing', 'high', 'in-progress', 'landlord', '2024-09-15T14:00:00Z', '2024-09-16T09:00:00Z', 'Mike''s Plumbing'
FROM leases l WHERE l.unit='Unit 2A';

-- Additional sample tickets
INSERT INTO maintenance_tickets (
  lease_id, issue, category, priority, status, responsibility, created_at, updated_at, assigned_to
) SELECT l.id, 'HVAC not cooling properly', 'hvac', 'medium', 'open', 'landlord', '2024-09-20T10:00:00Z', '2024-09-20T10:00:00Z', NULL
FROM leases l WHERE l.unit='Unit 3B';

INSERT INTO maintenance_tickets (
  lease_id, issue, category, priority, status, responsibility, created_at, updated_at, assigned_to
) SELECT l.id, 'Bathroom light flickers', 'electrical', 'low', 'resolved', 'landlord', '2024-09-10T08:30:00Z', '2024-09-12T17:45:00Z', 'Bright Electric Co.'
FROM leases l WHERE l.unit='Unit 2A';

INSERT INTO maintenance_tickets (
  lease_id, issue, category, priority, status, responsibility, created_at, updated_at, assigned_to
) SELECT l.id, 'Dishwasher making grinding noise', 'appliances', 'medium', 'open', 'shared', '2024-09-22T12:15:00Z', '2024-09-22T12:15:00Z', NULL
FROM leases l WHERE l.unit='Unit 3B';

COMMIT;
