# MCP Tools (Initial Contract)

This server is expected to expose these tools to the client agent.

## Sequential Thinking

- plan_prompt_to_steps(prompt: string) -> [{ step: string, rationale: string }]
- classify_issue(prompt: string) -> { category: string, priority: 'low'|'medium'|'high'|'urgent', responsibility_guess: 'tenant'|'landlord'|'shared'|'unknown' }

## Filesystem (Workflows)

- read_workflows() -> WorkflowEntry[]
- write_workflows(json: WorkflowEntry[]) -> void
- append_workflow_entry(entry: WorkflowEntry) -> void

Where `WorkflowEntry` is:

```
{
  id: string,
  createdAt: string, // ISO8601
  prompt: string,
  steps: { title: string, status: 'planned'|'done'|'error', note?: string }[],
  result?: { type: 'ticket'|'rent_details'|'other', data: any }
}
```

Target file: `frontend/Housing-Agent-Lovable/public/workflows.json` (UI reads this).

## SQLite

- get_rent_details(lease_id?: number, tenant_email?: string)
  -> { rent_amount: number, due_day: number, components: { label: string, amount_cents: number, included: boolean }[], summary: string }

- list_due_payments(reference_date?: string)
  -> [{ lease_id: number, tenant: string, amount_cents: number, due_date: string, status: 'due'|'overdue'|'paid' }]

- mark_payment_received(lease_id: number, amount_cents: number, paid_at: string, method: string, reference?: string)
  -> { payment_id: number }

- create_maintenance_ticket(lease_id?: number, tenant_email?: string, issue: string, category?: string, priority?: string, responsibility_guess?: string)
  -> { ticket_id: number }

- list_tickets(lease_id?: number, tenant_email?: string, tenant_id?: number, status?: string)
  -> Array<{ id: number, issue: string, category: string, priority: string, status: string, created_at: string, updated_at: string }>

- list_all_tickets(limit?: number)
  -> Array<{
       id: number,
       issue: string,
       category: string,
       priority: string,
       status: string,
       created_at: string,
       updated_at: string,
       assigned_to?: string,
       tenant: string,
       lease_unit: string
     }>

Refer to `data/schema.sql` for the table definitions.
