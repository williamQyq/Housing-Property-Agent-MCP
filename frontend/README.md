# Welcome to your Lovable project

## Project info

**URL**: https://lovable.dev/projects/ecf5bcec-fb2b-4287-834f-707a0b5306bd

## How can I edit this code?

There are several ways of editing your application.

**Use Lovable**

Simply visit the [Lovable Project](https://lovable.dev/projects/ecf5bcec-fb2b-4287-834f-707a0b5306bd) and start prompting.

Changes made via Lovable will be committed automatically to this repo.

**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes. Pushed changes will also be reflected in Lovable.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## Local Demo Setup (Master Server + MCP)

To run the full demo with the MCP master server and SQLite data:

1) Backend: Master Server

```
cd server-mcp/Housing-Property-Agent-MCP
pip install -r requirements.txt

# Initialize the SQLite database (one time)
sqlite3 data/app.db < data/schema.sql
sqlite3 data/app.db < data/seed.sql

# Start the FastAPI server
uvicorn master_server:app --host 0.0.0.0 --port 8000
```

2) Frontend: Environment

Create `frontend/Housing-Agent-Lovable/.env.local` with:

```
VITE_MASTER_SERVER_BASE=http://localhost:8000
# Demo identity (defaults to 1 if not set)
VITE_LEASE_ID=1
# Optional: used by chat request body for ticket creation
VITE_TENANT_EMAIL=sarah@example.com
# Optional: forward clone-specific voice/model to the NewportAI `/tts` proxy
# VITE_TTS_VOICE=David
# VITE_TTS_VOICE_ID=68f1011859224c3ead44e30ff5d735f2
# VITE_TTS_MODEL=tts-clone-model
# VITE_TTS_VOICE_NAME=David
```

3) Frontend: Run

```
cd frontend/Housing-Agent-Lovable
npm ci
npm run dev
```

What happens:
- TenantPortal Recent Requests loads from `GET /tenant/requests?leaseId=1` and renders items from SQLite.
- LandlordPortal loads requests from `GET /landlord/requests`.
- Chat tries `POST /chat/stream` for streaming updates and automatically falls back to `POST /chat`.
- The server uses MCP tools (and LLM if configured) and appends workflows to `public/workflows.json`.

## Troubleshooting

- 404 on `/tenant/requests`:
  - You’re likely running the wrong server. Start from `server-mcp/Housing-Property-Agent-MCP` with: `uvicorn master_server:app --host 0.0.0.0 --port 8000`.
  - Visit `http://localhost:8000/docs` and confirm `/tenant/requests` is listed.

- 404 on `/chat/stream`:
  - Indicates an older server build without the streaming route. The app will fall back to `/chat` automatically.

- 500 on `/chat`:
  - MCP tools not connected or DB missing. Ensure you initialized the DB and that the Python stdio servers can start (see `server_config.json`). On server startup, resolve any `[startup] Warning: MCP servers not connected` issues.

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/ecf5bcec-fb2b-4287-834f-707a0b5306bd) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/features/custom-domain#custom-domain)
