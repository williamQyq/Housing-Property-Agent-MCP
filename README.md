# Housing Agent MCP

Housing Agent MCP is a landlord-tenant assistant that pairs a React portal with a FastAPI master server orchestrating Model Context Protocol (MCP) tools. The system turns natural-language maintenance requests into actionable tickets, keeps both sides in sync with shared workflows, and optionally adds text-to-speech playback for responses.

## Key Features
- Tenant and landlord portals built with Vite, React, and shadcn UI components.
- FastAPI master server that brokers MCP tool calls to SQLite and filesystem backends.
- Workflow logging to `public/workflows.json` so both portals share planner and executor progress.
- Optional NewportAI-powered `/tts` endpoint for audio playback of assistant replies.
- Ready-to-run demo script and validation utilities for quick checks before a showcase.

## Repository Layout
- `frontend/Housing-Agent-Lovable/` - Vite app with tenant and landlord portals, chat UI, and workflow visualizations.
- `server-mcp/Housing-Property-Agent-MCP/` - FastAPI master server, SQLite database, and stdio MCP tool hosts.
- `start_demo.sh` - Spins up the master server and frontend (creates `.env.local` on first run).
- `validate_system.py`, `test_workflow_creation.py`, `simple_test.py` - Diagnostic scripts for end-to-end validation.
- `IMPLEMENTATION_SUMMARY.md`, `PROJECT.md`, `AGENTS.md` - Project history, goals, and agent coordination docs.

## System Architecture
1. Tenant submits a maintenance issue through the chat UI or form.
2. FastAPI master server receives the prompt and consults Anthropic (optional) plus MCP tool servers.
3. MCP tools classify the issue, create a maintenance ticket in SQLite, and append a workflow entry via the filesystem tool.
4. Frontend polls `/tenant/requests` and `/landlord/requests` to show ticket updates, and fetches `workflows.json` to render planner progress.
5. Optional `/tts` proxy turns assistant replies into audio without exposing API keys to the browser.

## Prerequisites
- Node.js 18+ and npm.
- Python 3.10+ (with `venv`) and the SQLite CLI (`sqlite3`).
- Optional NewportAI `NEWPORT_API_KEY` for real TTS output.
- Optional `ANTHROPIC_API_KEY` for LLM-driven planning; tests can run with `NO_LLM=1` to skip Anthropic calls.

## Quick Start
### Option 1 - Run the bundled demo
From the repository root:
```
./start_demo.sh
```
The script validates MCP connectivity, starts the master server on `http://localhost:8000`, creates `.env.local` if needed, installs frontend dependencies, and launches Vite on `http://localhost:5173`.

### Option 2 - Manual setup
**Backend (FastAPI + MCP):**
```
cd server-mcp/Housing-Property-Agent-MCP
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Initialize the demo database (run once)
sqlite3 data/app.db < data/schema.sql
sqlite3 data/app.db < data/seed.sql

# Run the master server (starts uvicorn internally)
python master_server.py
# alternatively
uvicorn master_server:app --host 0.0.0.0 --port 8000
```
`server_config.json` defines the stdio MCP tool processes (filesystem, SQLite, sequential reasoning). The master server loads it on startup and launches or monitors those tool workers automatically.

**Frontend (Vite + React):**
```
cd frontend/Housing-Agent-Lovable
npm ci
npm run dev
```
Create `.env.local` (or let `start_demo.sh` scaffold it) with:
```
VITE_MASTER_SERVER_BASE=http://localhost:8000
VITE_LEASE_ID=1
VITE_TENANT_EMAIL=sarah@example.com
```
Visit `http://localhost:5173` and choose the Tenant or Landlord portal to start exploring.

## Validation and Diagnostics
- `python validate_system.py` - Checks SQLite demo data, filesystem workflow writes, server config, and env files.
- `python test_workflow_creation.py` - Connects to MCP servers, drives a sample chat prompt, and verifies workflow plus ticket creation.
- `python simple_test.py` - Lightweight smoke test for filesystem workflow writes.

Run these from the repo root (activate the backend virtualenv first if you created one).

## Frontend Overview (`frontend/Housing-Agent-Lovable/src`)
- `pages/TenantPortal.tsx` - Two-column tenant dashboard with recent requests, chat assistant, and workflow activity feed.
- `pages/LandlordPortal.tsx` - Landlord view of all maintenance tickets with filtering and workflow insights.
- `hooks/useWorkflows.ts` - Polls `public/workflows.json` for planner and executor updates shared across portals.
- `components/ui/chat.tsx` - Chat surface that streams responses, appends new tickets, and can trigger `/tts` playback.

## MCP Servers and Tooling (`server-mcp/Housing-Property-Agent-MCP`)
- `mcp_servers/mcp_filesystem_server.py` - Appends workflow entries to the frontend `public/workflows.json` file.
- `mcp_servers/mcp_sqlite_server.py` - Reads and writes maintenance tickets, leases, and tenant data in SQLite.
- `mcp_servers/mcp_sequential_server.py` - Provides planning and classification helpers to guide workflows.
- `TOOLS.md` - Contract details for every exposed MCP tool (inputs, outputs, expectations).

Primary tools the master server expects include `classify_issue`, `create_maintenance_ticket`, `append_workflow_entry`, `list_tickets`, and related planner helpers.

## Workflow Data Contract
Workflows are appended to `frontend/Housing-Agent-Lovable/public/workflows.json` as an array of entries with the shape:
```
{
  "id": "string",
  "createdAt": "ISO8601 timestamp",
  "prompt": "original user prompt",
  "steps": [ { "title": "string", "status": "planned|done|error", "note"?: "string" } ],
  "result": { "type": "ticket|rent_details|other", "data": { ... } }
}
```
Keep planner updates in sync with `server-mcp/Housing-Property-Agent-MCP/PLAN.md` and ensure executor steps append (never overwrite) entries.

## Environment Variables
**Frontend (`.env.local`):**
- `VITE_MASTER_SERVER_BASE` - URL of the FastAPI master server (defaults to `http://localhost:8000`).
- `VITE_LEASE_ID` - Demo lease ID (defaults to `1`).
- `VITE_TENANT_EMAIL` - Email injected into chat requests when tickets are created.
- `VITE_TTS_VOICE` - Optional NewportAI clone voice identifier to request from the `/tts` proxy.
- `VITE_TTS_MODEL` - Optional NewportAI model override propagated to the `/tts` proxy.
- `VITE_TTS_VOICE_ID` - Optional NewportAI clone voice ID forwarded to the `/tts` proxy.
- `VITE_TTS_VOICE_NAME` - Optional explicit voice display name when it differs from `VITE_TTS_VOICE`.

**Backend:**
- `ANTHROPIC_API_KEY` - Optional; enables LLM-backed planning. Use `NO_LLM=1` when running tests without network access.
- `NEWPORT_API_KEY`, `NEWPORT_TTS_URL`, `TTS_MODEL`, `TTS_VOICE`, `TTS_VOICE_ID`, `TTS_VOICE_NAME` - Configure the `/tts` proxy for NewportAI (defaults target the Do TTS Clone endpoint).

## API Endpoints (FastAPI Master Server)
- `POST /chat` - Processes a maintenance prompt and returns a combined response.
- `POST /chat/stream` - Streams chat responses (frontend falls back to `/chat` if unavailable).
- `GET /tenant/requests?leaseId=1` - Recent maintenance tickets for a tenant.
- `GET /landlord/requests` - All maintenance tickets with status metadata.
- `POST /tts` - Optional TTS proxy for NewportAI voices.
- `GET /phone/twiml`, `GET /phone/audio/{filename}` - Assets for phone flows (not required for the core demo).

Visit `http://localhost:8000/docs` to explore the automatically generated OpenAPI docs.

## Troubleshooting
- **404 on `/tenant/requests`** - Ensure the master server is running from `server-mcp/Housing-Property-Agent-MCP` and the SQLite DB has been initialized.
- **500 on `/chat`** - MCP tool servers failed to start or the database is missing. Reinstall dependencies, verify `server_config.json`, and rerun the SQLite seed scripts.
- **502 on `/tts`** - Provide a `NEWPORT_API_KEY`; without it the server responds with 502 so you can debug TTS configuration.
- **Workflows not updating** - Confirm the filesystem MCP server is using the correct path to `public/workflows.json` and that the file remains a JSON array.

## Additional Resources
- `IMPLEMENTATION_SUMMARY.md` - Chronological list of fixes and enhancements.
- `PROJECT.md` - Vision, goals, and potential extensions beyond the demo scope.
- `server-mcp/Housing-Property-Agent-MCP/PLAN.md` - Planner and executor coordination for workflow updates.

Feel free to customize tool prompts, expand the MCP tool surface, or add Vitest tests under `frontend/Housing-Agent-Lovable/src/__tests__/` as the next iteration.
