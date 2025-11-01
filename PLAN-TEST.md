# Test Strategy & Organization Plan

## 1. Objectives
- Establish a consistent testing approach for both the React frontend (`frontend/`) and the FastAPI MCP server (`server-mcp/`).
- Ensure core user flows (tenant + landlord portals) are covered by fast unit/component tests before adding heavier integration coverage.
- Provide a maintainable structure so future agents can add tests without guessing where files or configs live.

## 2. Current State Assessment
- Frontend has no test runner configured; `package.json` lacks a `test` script. Vite/Vitest is the natural fit.
- Server code relies on FastAPI + SQLite, but no pytest configuration or fixtures exist yet.
- Root repo already has a few helper scripts (e.g., `verify_tenant_requests.py`); we will treat these as ad-hoc tools, not formal tests.

## 3. Tooling Decisions
- **Frontend**: Add Vitest + React Testing Library. They integrate smoothly with Vite and support jsdom for component rendering.
- **Server**: Adopt Pytest with `httpx.AsyncClient` for FastAPI endpoint tests and `pytest-asyncio` for async fixtures.
- **Cross-cutting utilities**: Use Playwright (optional future milestone) for full-stack smoke tests once core unit coverage is in place.

## 4. Directory Layout & Naming
- `frontend/src/components/**`: co-locate unit specs as `ComponentName.test.tsx` next to the component for tight coupling and easier refactors.
- `frontend/src/pages/__tests__/`: hold higher-level page tests (render + data-loading stubs) so routing-focused suites stay grouped.
- `frontend/src/__tests__/integration/`: for multi-component flows (e.g., tenant request timeline) that need shared mocks.
- `frontend/test/setup/`: centralize Vitest setup files (jsdom, RTL helpers, MSW server config if added later).
- `server-mcp/tests/unit/`: isolated function tests (utility modules, tool adapters).
- `server-mcp/tests/api/`: FastAPI route tests using `TestClient`/`AsyncClient` and database fixtures.
- `server-mcp/tests/fixtures/`: reusable pytest fixtures (DB seeding, temporary files). Keep `__init__.py` minimal so pytest treats them as packages.
- Reserve `tests/e2e/` at repo root for future Playwright or contract tests that span both modules; this stays empty until end-to-end coverage becomes a priority.

## 5. Configuration & Scripts
- Frontend `package.json`: add `test`, `test:watch`, and `test:coverage` scripts; configure Vitest via `vitest.config.ts` extending Vite config.
- Server `pyproject.toml`: add dev-dependencies (`pytest`, `pytest-asyncio`, `httpx`, `faker`, `pytest-cov`). Provide a `scripts/test` helper in `README`.
- Root-level convenience shell script `./scripts/test-all.sh`: orchestrates `npm test` inside `frontend/` and `pytest` inside `server-mcp/`.
- Enforce coverage thresholds later; start by generating reports (`frontend/coverage/`, `server-mcp/htmlcov/`).

## 6. Test Data & Fixtures
- Frontend: use MSW to mirror API responses from the Master Server; seed handlers with `tenant/requests` and `landlord/requests` examples.
- Server: create fixture to load SQLite schema + seed data into a temporary DB (copy from `data/app.db` or run migrations against `tmp_path`).
- Document fixture behavior in `server-mcp/tests/README.md` so contributors know how data resets between tests.

## 7. Implementation Milestones
1. **Bootstrap Tooling**
   - Add Vitest + RTL dependencies, config, and sample smoke test (e.g., `App.test.tsx`).
   - Add pytest dependencies, base config, and sanity check test for `/tenant/requests` route.
2. **Core Coverage**
   - Frontend: cover critical UI widgets (request timeline, modals, workflow submission forms).
   - Server: validate happy-path + error-path for tenant/landlord endpoints, including empty datasets.
3. **Integration Enhancements**
   - Introduce MSW for consistent API mocking.
   - Provide database fixture to run tests against in-memory SQLite where feasible.
4. **Automation & Reporting**
   - Wire scripts into CI (GitHub Actions or manual instructions) once coverage stabilizes.
   - Track coverage trends and raise thresholds incrementally.

## 8. Governance & Maintenance
- Each new feature PR must include or update relevant tests in the matching module.
- Keep setup helpers small and shared via `test-utils.tsx` or pytest fixtures to avoid duplication.
- Update this plan when introducing new test types (e2e, contract tests) or when folder layout evolves.
- Store troubleshooting notes in `PLAN-TEST.md` to help future agents debug flaky tests or environment assumptions.

## 9. Open Questions / Follow-ups
- Decide if we need Playwright right away or only after unit/integration coverage lands.
- Confirm acceptable coverage baseline with stakeholders (suggest starting at 70% statements for both modules).
- Determine whether to mirror server tests inside the FastAPI repo’s own CI or rely solely on the shared script.

