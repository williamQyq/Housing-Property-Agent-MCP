# Repository Guidelines

## Project Structure & Module Organization
- Root modules: `frontend/` (React + Vite app) and `server-mcp/` (MCP server repo).
- Frontend app: `frontend/Housing-Agent-Lovable/`
  - Source: `src/` (components in `src/components/ui`, pages in `src/pages`, hooks in `src/hooks`, utilities in `src/lib`).
  - Assets: `src/assets/`; public files: `public/`.
- MCP server: `server-mcp/Housing-Property-Agent-MCP/` (managed separately; see its `README.md`).

## Build, Test, and Development Commands
- Dev (frontend): `cd frontend/Housing-Agent-Lovable && npm ci && npm run dev` — start Vite dev server.
- Lint: `npm run lint` — ESLint checks TypeScript/React code.
- Build: `npm run build` — production build to `dist/`.
- Preview: `npm run preview` — serve the built app locally.

## Coding Style & Naming Conventions
- Language: TypeScript + React. Indentation: 2 spaces; keep lines focused and self-documenting.
- Components: PascalCase files in `src/components` (e.g., `Button.tsx`).
- Pages: PascalCase in `src/pages` (e.g., `TenantPortal.tsx`).
- Hooks: `use-*.tsx` or `use*.ts(x)` in `src/hooks` (e.g., `use-mobile.tsx`).
- Utilities: `camelCase` in `src/lib` (e.g., `utils.ts`).
- Linting: ESLint configured via `eslint.config.js`. Fix warnings before PRs.

## Testing Guidelines
- No test framework is configured yet. If adding tests, prefer Vitest + React Testing Library.
- Place tests alongside sources or under `src/__tests__/` as `*.test.ts(x)`.
- Ensure critical components and hooks have basic render and behavior tests.

## Commit & Pull Request Guidelines
- Commits: small, focused, imperative mood (e.g., "Add tenant portal card"). Conventional Commits are encouraged (`feat:`, `fix:`, `chore:`).
- Before PR: run `npm run lint` and `npm run build`. Include screenshots/GIFs for UI changes.
- PRs: clear description, linked issues, scope of change, and any breaking notes.

## Security & Configuration Tips
- Frontend env vars must be prefixed with `VITE_` and stored in `.env.local` (do not commit). Example: `VITE_API_BASE=https://api.example.com`.
- Avoid secrets in client code or git history. Server configuration lives under `server-mcp/` and should follow its README.

## Agent-Specific Instructions
- Do not rename folders or move files across modules unless requested.
- Touch only files relevant to the task; preserve existing coding patterns and imports.

## Overview
This system implements a dual-role approach for handling complex tasks through coordinated planning and execution.
 
## Roles
 
### Planner
- Analyzes user requirements and breaks them down into actionable steps
- Creates detailed execution plans
- Identifies potential challenges and dependencies
- Validates feasibility of proposed solutions
- Maintains high-level project vision
 
### Executor
- Implements the planned steps
- Provides real-time feedback on implementation progress
- Identifies technical challenges during execution
- Suggests adjustments to the plan based on practical constraints
- Ensures code quality and best practices
 
## Role Switching Criteria
 
### Switch to Planner when:
- New requirements are introduced
- Current plan needs significant revision
- Multiple implementation options need evaluation
- Complex dependencies need to be resolved
- Project scope or direction needs reassessment
 
### Switch to Executor when:
- Clear plan is established
- Technical implementation is straightforward
- Immediate action is required
- Debugging or optimization is needed
- Code review or refactoring is necessary
 
## Decision Making Process
1. Analyze current context and requirements
2. Determine if planning or execution is needed
3. Switch to appropriate role
4. Execute role-specific responsibilities
5. Validate outcomes
6. Document decisions and progress
7. Repeat process as needed
 
## Validation Steps
- Verify alignment with project goals
- Check technical feasibility
- Ensure code quality standards
- Validate against user requirements
- Review for potential issues or edge cases
 
## Feedback Loop
- Regular progress updates
- Documentation of decisions and rationale
- Continuous validation of approach
- Adaptation based on new information
- User feedback integration
 
## Best Practices
- Maintain clear communication between roles
- Document all significant decisions
- Regular progress reviews
- Proactive issue identification
- Continuous improvement of processes

## Workflow Synchronization
- Planner converts user goals into concrete workflow steps inside `PLAN.md`, ensuring they map cleanly to the `workflows.json` schema.
- Executor coordinates with the filesystem MCP tool so planner-approved steps append to `frontend/Housing-Agent-Lovable/public/workflows.json` without overwriting existing entries.
- Both roles confirm the workflow payload includes `id`, `createdAt`, `prompt`, `steps`, and `result` fields so the frontend can render progress accurately.

## Documentation Updates
- Refresh `PLAN.md` whenever scope or sequencing changes so the filesystem workflow stays consistent with the documented plan.
- Record MCP integration adjustments (e.g., new tool names or parameters) in this file to keep future agents aligned.

## Demo Identity & Recent Requests
- Demo tenant and lease
  - tenant_id: 1
  - lease_id: 1
- Frontend configuration
  - `VITE_MASTER_SERVER_BASE` should point to the running Master Server (e.g., `http://localhost:8000`).
  - `VITE_LEASE_ID` may be set to `1`, but the app defaults to `1` for local demos.
- Data flow
  - TenantPortal Recent Requests loads from the Master Server via `GET /tenant/requests?leaseId=1`, which proxies to the SQLite MCP server.
  - LandlordPortal loads all maintenance requests via `GET /landlord/requests`.
  - Workflows are appended by the Filesystem MCP to `frontend/Housing-Agent-Lovable/public/workflows.json` when maintenance prompts are processed.
  - If you see `404 Not Found` for `/tenant/requests`, confirm you started the correct app: run `uvicorn master_server:app --host 0.0.0.0 --port 8000` from `server-mcp/Housing-Property-Agent-MCP`, then hit `http://localhost:8000/tenant/requests?leaseId=1`.

## Troubleshooting
- 500 on `POST /chat`
  - Cause: MCP tools not connected (e.g., Python MCP servers didn’t start) or DB not initialized.
  - Fix:
    - Ensure Python has the `modelcontextprotocol` (mcp) package installed.
    - Ensure the DB exists: from `server-mcp/Housing-Property-Agent-MCP`, run:
      - `sqlite3 data/app.db < data/schema.sql`
      - `sqlite3 data/app.db < data/seed.sql`
    - Start the master server as above. On startup you may see `[startup] Warning: MCP servers not connected: ...` if tool processes failed; resolve those errors.
    - Verify tools are available via `/docs` and by calling `GET /tenant/requests?leaseId=1`.

- Frontend cannot reach server
  - Check `.env.local` in `frontend/Housing-Agent-Lovable` and set `VITE_MASTER_SERVER_BASE=http://localhost:8000`.
  - The app also honors `window.__MASTER_SERVER_BASE` and localStorage key `VITE_MASTER_SERVER_BASE`.
