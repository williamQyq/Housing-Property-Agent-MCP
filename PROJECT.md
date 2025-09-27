🏠 Landlord–Tenant MCP Agent
A Hackathon Project — Complement to Zillow

🔑 Core Idea
Zillow already covers listing, pricing, and search. What it doesn’t address is the ongoing relationship once a tenant moves in: handling maintenance requests, communication, payments, and compliance.
Our project uses Model Context Protocol (MCP) to bridge this gap. MCP allows us to expose tools and workflows(like ticketing, notifications, or document parsing) that an LLM agent can call on behalf of landlords and tenants. The result: a lightweight but powerful assistant that improves day-to-day rental management.

🎯 Goals
Reduce friction in landlord–tenant communication.
Automate repetitive or stressful tasks (maintenance requests, reminders).
Provide clarity on responsibility (tenant vs landlord).
Stay small and hackathon-ready: focus on 1–2 core MCP tools.

🚀 Feature Ideas
1. Smart Maintenance Request Agent
Flow: Tenant describes issue in plain language → LLM classifies urgency + category → MCP tools log and notify.
MCP Tools:
create_ticket(issue, priority, category) → saves to SQLite/Google Sheet.
notify_landlord(ticket_id) → sends email/SMS.
find_repair_service(category) → queries API or mock db.
Bonus: Suggests responsibility (tenant vs landlord).

2. Mini Dispute & Compliance Helper
Upload receipts or notes from both sides.
Agent checks housing rules (mock legal data).
Output: concise summary (“Boiler repair = landlord responsibility; repainting = tenant responsibility”).
Value: Zillow doesn’t cover this legal/compliance angle.

3. Auto-Translate & Summarize Requests
Problem: Tenants and landlords may not share a language.
Solution: Agent translates + simplifies.
Example: “La caldera no calienta bien” → “Heating system not producing hot water (boiler issue, urgent).”

4. Rental Document Companion
MCP Tools:
upload_lease(file)
extract_key_terms(lease) → rent, due date, penalties.
remind_due_date() → alert tenant/landlord.
Use cases:
Tenant: “When is my rent due?”
Landlord: “What repairs am I obligated to cover?”

5. Repair Cost Estimator
Tenant logs a problem (“leaking faucet”).
Agent calls cost API (or mock db).
Returns estimate + handyman contacts.

🛠️ Hackathon Scope (Keep It Small)
Implement 1–2 MCP tools:
create_ticket
notify_landlord
Storage: JSON file or Google Sheets.
Interface:
CLI chatbot or simple React UI.
Tenants type requests → Agent → Tools.
Stretch goal: add translation or cost estimator.

🧩 Architecture
Tenant → LLM Agent (client) → MCP Server (tools) → Storage/Notifications

MCP Client: LLM interprets text, decides which tool to call.
MCP Server: Exposes tools (create_ticket, notify_landlord, …).
Backend: SQLite/JSON + mock APIs for costs/repairs.
