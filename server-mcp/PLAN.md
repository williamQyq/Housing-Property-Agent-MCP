TTS Playback Plan

- Goal: Add voice playback for LLM responses in the frontend using NewportAI “Do TTS Common”.

Milestones (Completed)

- Add API: Created FastAPI endpoint `/tts` that accepts text and returns audio bytes.
- Reuse TTS: Reused NewportAI TTS logic from `mcp_phone_tts_server.py`.
- Auth + config: Reads `NEWPORT_API_KEY`, optional `NEWPORT_TTS_URL`, `TTS_MODEL`, `TTS_VOICE`.
- MIME types: Returns proper `Content-Type` for `mp3|wav|ogg`.
- Frontend hook: Added a Play button in `src/components/ui/chat.tsx` that calls `/tts` and plays audio.
- Docs: Updated README with endpoint description and usage example.

Notes

- The frontend repository lives outside this repo; patch applied directly to `frontend/Housing-Agent-Lovable`.
- The NewportAI key remains server-side; the frontend calls our `/tts` proxy.
- Without `NEWPORT_API_KEY`, the server falls back to silent WAV for local testing; playback still works.

Debugging /tts 500

- Common causes: missing `NEWPORT_API_KEY`, network-restricted environment, or incorrect `NEWPORT_TTS_URL`.
- Behavior change: `/tts` now falls back to generating a short silent WAV on TTS errors (network/API failures) instead of returning 500.
- Headers: responses that used fallback include `X-TTS-Fallback: true` and a truncated `X-TTS-Error` for context.
- Next steps if fallback triggers: verify env vars, double-check outbound network access, or set `NEWPORT_TTS_URL` to the correct endpoint.
