"""
Simple test script to call the phone-tts MCP server tools via stdio.

Usage examples:
  python3 scripts/test_phone_tts.py --to +15551234567 --text "Hello from NewportAI TTS" \
    --voice alloy --model tts-1 --format mp3

Required env vars for real calls:
  - TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER
  - BASE_URL (public URL resolving to master_server; e.g., https://<ngrok-id>.ngrok.io)
  - NEWPORT_API_KEY (and NEWPORT_TTS_URL if the default placeholder is incorrect)

For TTS-only dry run, pass --dry which creates a silent WAV locally, but Twilio call still requires env.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


def abs_repo_path(*parts: str) -> str:
    return str(Path(__file__).resolve().parents[1].joinpath(*parts))


async def main() -> None:
    parser = argparse.ArgumentParser(description="Test phone-tts MCP server")
    parser.add_argument("--to", dest="to", required=True, help="Destination E.164 phone number e.g., +15551234567")
    parser.add_argument("--text", dest="text", required=True, help="Text to speak")
    parser.add_argument("--voice", dest="voice", default=None)
    parser.add_argument("--model", dest="model", default=None)
    parser.add_argument("--format", dest="fmt", default="mp3", choices=["mp3", "wav", "ogg"])
    parser.add_argument("--sample-rate", dest="rate", type=int, default=None)
    parser.add_argument("--dry", dest="dry", action="store_true", help="Generate local silence instead of real TTS")
    parser.add_argument("--followup-text", dest="followup", default=None, help="Optional second clip to play via speak_text")
    parser.add_argument("--followup-delay", dest="delay", type=int, default=10, help="Seconds to wait before follow-up")
    parser.add_argument("--python", dest="py", default=None, help="Python executable to run the MCP server")
    args = parser.parse_args()

    py_exec = args.py or os.environ.get("PYTHON", "python3")
    server_script = abs_repo_path("mcp_servers", "mcp_phone_tts_server.py")

    params = StdioServerParameters(command=py_exec, args=[server_script])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Start call
            start_payload: Dict[str, Any] = {
                "phone_number": args.to,
                "text": args.text,
                "voice": args.voice,
                "model": args.model,
                "format": args.fmt,
                "sample_rate_hz": args.rate,
                "dry_run": bool(args.dry),
            }
            print("[test] Calling start_call with:")
            print(json.dumps(start_payload, indent=2))
            result = await session.call_tool("start_call", arguments=start_payload)
            print("[test] start_call result (raw):")
            print(result)

            # Extract call identifiers for optional speak_text
            # Try to extract structured content first
            call_id = None
            call_sid = None
            try:
                sc = getattr(result, "structuredContent", None)
                if isinstance(sc, dict):
                    call_id = sc.get("callId") or call_id
                    call_sid = sc.get("twilioCallSid") or call_sid
            except Exception:
                pass

            # Fallback: parse content blocks as JSON
            if not (call_id and call_sid):
                try:
                    blocks = result.content or []
                    payload = None
                    for b in blocks:
                        text_val = getattr(b, "text", None)
                        if isinstance(text_val, str):
                            try:
                                payload = json.loads(text_val)
                                break
                            except Exception:
                                pass
                    if isinstance(payload, dict):
                        call_id = payload.get("callId") or call_id
                        call_sid = payload.get("twilioCallSid") or call_sid
                except Exception:
                    pass

            if args.followup and call_id and call_sid:
                import asyncio as _asyncio
                print(f"[test] Waiting {args.delay}s before follow-up speak_text...")
                await _asyncio.sleep(max(0, int(args.delay)))
                speak_payload = {
                    "call_id": call_id,
                    "twilio_call_sid": call_sid,
                    "text": args.followup,
                    "voice": args.voice,
                    "model": args.model,
                    "format": args.fmt,
                    "sample_rate_hz": args.rate,
                    "dry_run": bool(args.dry),
                }
                print("[test] Calling speak_text with:")
                print(json.dumps(speak_payload, indent=2))
                speak_res = await session.call_tool("speak_text", arguments=speak_payload)
                print("[test] speak_text result (raw):")
                print(speak_res)


if __name__ == "__main__":
    asyncio.run(main())
