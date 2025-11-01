# Repository Guidelines

## Project Structure & Module Organization
- Root modules: `frontend/` (React + Vite application) and `services/` (microservices architecture).
- Frontend app lives directly under `frontend/`.
  - Core source: `frontend/src/`
    - UI components in `src/components/ui`
    - Pages in `src/pages`
    - Hooks in `src/hooks`
    - Utilities in `src/lib`
  - Static assets: `src/assets/`
  - Public files (including `workflows.json`): `frontend/public/`
- Microservices architecture: `services/`
  - BFF service: `services/bff/` (Go)
  - Identity service: `services/identity/` (Go)
  - Orchestrator service: `services/orchestrator/` (Go)
  - Agent/MCP service: `services/agent-mcp/` (Python)
  - Payment service: `services/payment-service/` (Java Spring Boot)
- Legacy data: `data/legacy/` (preserved SQLite schema and seed data)
- Utility scripts (e.g., validation, demo startup) are in the repo root.

## Build, Test, and Development Commands
- Frontend dev: `cd frontend && npm ci && npm run dev`
- Frontend lint: `cd frontend && npm run lint`
- Frontend build: `cd frontend && npm run build`
- Frontend preview: `cd frontend && npm run preview`
- BFF service: `cd services/bff && go run main.go`
- Identity service: `cd services/identity && go run main.go`
- Orchestrator service: `cd services/orchestrator && go run main.go`
- Agent/MCP service: `cd services/agent-mcp && uv run python main.py`
- Payment service: `cd services/payment-service && mvn spring-boot:run`

## Coding Style & Naming Conventions
- TypeScript + React with 2-space indentation; keep code concise and self-documenting.
- Components: PascalCase files under `src/components` (e.g., `ChatPanel.tsx`).
- Pages: PascalCase under `src/pages` (e.g., `TenantPortal.tsx`).
- Hooks: `use*.ts(x)` under `src/hooks` (e.g., `useTenantRequests.ts`).
- Utilities: `camelCase.ts` under `src/lib`.
- Follow existing import patterns; prefer relative paths scoped to `src/` aliases if already configured.

## Testing Guidelines
- No automated tests exist yet; prefer Vitest + React Testing Library if you add any.
- Store tests alongside sources or under `src/__tests__/` with `*.test.ts(x)` suffix.
- Cover critical UI flows and hooks (render + basic behavior) when adding tests.

## Commit & Pull Request Guidelines
- Author focused commits in imperative mood (Conventional Commit prefixes encouraged).
- Run `npm run lint` and `npm run build` from `frontend/` before PRs.
- Provide screenshots or GIFs for UI changes when opening a PR.

## Security & Configuration Tips
- Frontend env vars belong in `frontend/.env.local` (never commit); they must be prefixed with `VITE_`.
  - Example entries: `VITE_MASTER_SERVER_BASE=http://localhost:8000`, `VITE_LEASE_ID=1`, `VITE_TENANT_EMAIL=sarah@example.com`.
- Protect secrets: keep API keys and database files out of version control. Service configurations live under `services/` and should follow their respective READMEs.

## Agent-Specific Instructions
- Do not rename top-level folders or move modules across `frontend/` and `services/` unless explicitly asked.
- Touch only files relevant to the task; leave unrelated user changes intact.
- Use `rg` for searching within the repo (faster than `grep`).

## Development Workflow
This project uses a microservices architecture with clear separation of concerns.

### Service Responsibilities
- **BFF Service**: Central API gateway, handles authentication and routing
- **Identity Service**: User authentication, OTP management, phone verification
- **Orchestrator Service**: Room management, user invitations, business logic
- **Agent/MCP Service**: AI tool execution, LLM integration, guardrails
- **Payment Service**: Payment processing, transaction management

### Development Process
- Each service is independently deployable and testable
- Services communicate via REST APIs
- Frontend consumes BFF service APIs
- All services are containerized and Kubernetes-ready

## Data Management
- Legacy SQLite data preserved in `data/legacy/`
- New architecture uses PostgreSQL for core data
- Redis for caching and session management
- All sensitive data managed via Kubernetes secrets

## Demo Identity & Data Flow
- Demo tenant/lease IDs remain `tenant_id=1`, `lease_id=1` in PostgreSQL.
- Tenant Portal fetches data from BFF service, which routes to appropriate microservices.
- Landlord Portal hits BFF service for all maintenance tickets and room management.
- AI chat interface uses Agent/MCP service for tool execution and responses.

## Troubleshooting
- `404 /api/*`: Ensure BFF service is running on port 8080
- `500 /api/agent/*`: Check Agent/MCP service is running on port 8083
- `401 Unauthorized`: Verify Identity service is running and JWT tokens are valid
- Frontend cannot reach services: verify service URLs in `frontend/.env.local`
