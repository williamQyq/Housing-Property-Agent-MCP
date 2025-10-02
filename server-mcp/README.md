# Nest --- Housing-Property-Agent-MCP

MCP server for the Landlord–Tenant agent. This repo exposes tools for planning, filesystem updates, and SQLite reads/writes.

## Data

- SQLite DB path: `data/app.db`
- Schema: `data/schema.sql`
- Seed: `data/seed.sql`

Create the database locally with the SQLite CLI:

```
sqlite3 data/app.db < data/schema.sql
sqlite3 data/app.db < data/seed.sql
```

## Filesystem Tool Target

- Frontend workflows file: `../..//frontend/Housing-Agent-Lovable/public/workflows.json`
  - JSON array of workflow entries written by the Filesystem MCP tool.

## Tools (contracts)

See `TOOLS.md` for the initial tool surface and contracts.

## MCP Servers (stdio)

Three stdio MCP servers are provided in `mcp_servers/`:

- Filesystem: reads/writes the frontend workflows file
  - `mcp_servers/mcp_filesystem_server.py`
- Sequential Thinking: planning + issue classification
  - `mcp_servers/mcp_sequential_server.py`
- SQLite: rent details, due payments, maintenance tickets
  - `mcp_servers/mcp_sqlite_server.py`

Top-level `server_config.json` is provided to be used by your MCP client (like the deeplearning.ai example). It launches each server via `python3` with stdio transport.

Prereqs: `python3` with the `mcp` package installed (modelcontextprotocol Python lib).

Run the client (example outline):

1. Initialize the DB (one-time)
   - `sqlite3 data/app.db < data/schema.sql`
   - `sqlite3 data/app.db < data/seed.sql`
2. From repo root, run your MCP client that reads `server_config.json` (see the example in the prompt).

## TTS Playback (Frontend Integration)

This server exposes a proxy endpoint to synthesize speech via NewportAI TTS (clone endpoint) without exposing your API key to the browser. If synthesis fails (missing key, network error, invalid voice), the endpoint returns `502` with an explanatory message so you can diagnose instead of receiving silent audio.

- Endpoint: `POST /tts`
- Body: `{ text: string, format?: 'mp3'|'wav'|'ogg', voice?: string, model?: string, sample_rate_hz?: number, dry_run?: boolean }`
- Returns: audio bytes with appropriate `Content-Type` (e.g., `audio/mpeg`)

Environment variables:

- `NEWPORT_API_KEY` – required (set via environment, do not commit)
- `NEWPORT_TTS_URL` – optional override (defaults to NewportAI's Do TTS Clone endpoint)
- `TTS_MODEL` – optional default model
- `TTS_VOICE` – optional default voice name
- `TTS_VOICE_ID` – optional default clone voice ID
- `TTS_VOICE_NAME` – optional explicit display name if different from `TTS_VOICE`

Example frontend usage (React/vanilla):

```ts
async function speak(text) {
  const res = await fetch("/tts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      format: "mp3",
      voice: "David", // optional voice name
      voiceId: "68f1011859224c3ead44e30ff5d735f2" // optional voice ID
    })
  });
  if (!res.ok) throw new Error("TTS failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  audio.play();
}

// After you render the LLM response text:
// speak(result.text)
```

If your frontend runs on a different origin, ensure CORS is configured appropriately.
