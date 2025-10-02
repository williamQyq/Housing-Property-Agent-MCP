from __future__ import annotations

import base64
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from mcp.server.fastmcp import FastMCP as Server


server = Server("phone-tts-mcp")


# Storage paths
REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIO_DIR = REPO_ROOT / "data" / "phone_audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.environ.get(name)
    return val if (val and str(val).strip()) else default


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


def _make_silence_wav(duration_sec: float = 1.0, sample_rate: int = 8000) -> bytes:
    import struct
    n_samples = int(duration_sec * sample_rate)
    byte_rate = sample_rate * 1 * 2  # mono, 16-bit
    block_align = 1 * 2
    data_bytes = b"".join(struct.pack("<h", 0) for _ in range(n_samples))
    # RIFF/WAVE header
    riff_chunk_size = 36 + len(data_bytes)
    header = b"RIFF" + struct.pack("<I", riff_chunk_size) + b"WAVE"
    fmt_chunk = (
        b"fmt "
        + struct.pack("<I", 16)  # PCM chunk size
        + struct.pack("<H", 1)  # PCM format
        + struct.pack("<H", 1)  # channels
        + struct.pack("<I", sample_rate)
        + struct.pack("<I", byte_rate)
        + struct.pack("<H", block_align)
        + struct.pack("<H", 16)  # bits per sample
    )
    data_chunk = b"data" + struct.pack("<I", len(data_bytes)) + data_bytes
    return header + fmt_chunk + data_chunk


def _twilio_base_url() -> str:
    return "https://api.twilio.com/2010-04-01"


def _http_post(url: str, auth: Optional[tuple[str, str]] = None, data: Optional[Dict[str, str]] = None,
               headers: Optional[Dict[str, str]] = None, json_body: Optional[Dict[str, Any]] = None) -> tuple[int, bytes, Dict[str, str]]:
    # Minimal HTTP POST using urllib to avoid extra deps
    import urllib.request
    import urllib.error

    req_headers = headers.copy() if headers else {}
    body: bytes
    if json_body is not None:
        body = json.dumps(json_body).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    else:
        # form-encoded
        from urllib.parse import urlencode
        body = urlencode(data or {}).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

    req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
    if auth:
        user, pwd = auth
        token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:  # pragma: no cover - network path
        return e.code, e.read(), dict(e.headers)


def _http_post_binary(url: str, headers: Dict[str, str], body: bytes) -> tuple[int, bytes, Dict[str, str]]:
    import urllib.request
    import urllib.error
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:  # pragma: no cover - network path
        return e.code, e.read(), dict(e.headers)


def _looks_like_base64(value: str) -> bool:
    candidate = value.strip()
    if candidate.startswith("data:"):
        parts = candidate.split(",", 1)
        if len(parts) == 2:
            candidate = parts[1]
    if len(candidate) < 48:
        return False
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r")
    return all(c in allowed for c in candidate)


def _decode_audio_payload(payload: Any) -> Optional[bytes]:
    """Attempt to extract base64 encoded audio bytes from an arbitrary payload."""

    def iter_strings(node: Any, path: str = "") -> Iterable[str]:
        if isinstance(node, dict):
            for key, val in node.items():
                next_path = f"{path}.{key}" if path else key
                yield from iter_strings(val, next_path)
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                next_path = f"{path}[{idx}]"
                yield from iter_strings(item, next_path)
        elif isinstance(node, str):
            lowered = path.lower()
            if any(token in lowered for token in ("audio", "data", "content", "payload")) and _looks_like_base64(node):
                yield node

    for candidate in iter_strings(payload):
        cleaned = candidate.strip()
        if cleaned.startswith("data:"):
            cleaned = cleaned.split(",", 1)[-1]
        try:
            audio_bytes = base64.b64decode(cleaned, validate=False)
        except Exception:
            continue
        if audio_bytes:
            return audio_bytes
    return None


def synthesize_tts(
    text: str,
    *,
    model: Optional[str] = None,
    voice: Optional[str] = None,
    voice_id: Optional[str] = None,
    voice_name: Optional[str] = None,
    voice_clone_id: Optional[str] = None,
    fmt: str = "mp3",
    sample_rate_hz: Optional[int] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Call NewportAI Do TTS Clone API; return saved file metadata.

    In dry_run or when no NEWPORT_API_KEY provided, generate a short silence WAV.
    """
    message_id = _new_id("msg")
    ext = fmt.lower().strip()
    if ext not in {"mp3", "wav", "ogg"}:
        ext = "mp3"
    file_path = AUDIO_DIR / f"{message_id}.{ext}"

    api_key = _env("NEWPORT_API_KEY")
    endpoint = _env("NEWPORT_TTS_URL")  # if not set, fall back to clone endpoint per docs
    if not endpoint:
        endpoint = "https://api.newportai.com/do-tts-clone"

    if dry_run:
        # Create a brief silence WAV for explicit dry runs (testing only)
        data = _make_silence_wav(1.0)
        if ext != "wav":
            file_path = AUDIO_DIR / f"{message_id}.wav"
            ext = "wav"
        _write_bytes(file_path, data)
        return {"messageId": message_id, "path": str(file_path), "ext": ext, "bytes": len(data), "dry": True}

    if not api_key:
        raise RuntimeError("NEWPORT_API_KEY is not configured; set it to enable NewportAI TTS")

    # Build request according to NewportAI TTS clone spec; may need adjustment with exact API
    resolved_voice_name = voice_name or voice or _env("TTS_VOICE_NAME") or _env("TTS_VOICE")
    resolved_voice_id = voice_id or voice_clone_id or _env("TTS_VOICE_ID") or _env("TTS_VOICE_CLONE_ID")
    payload: Dict[str, Any] = {
        "input": text,
        "format": ext,
        "model": model or _env("TTS_MODEL") or "tts-1",
    }
    if resolved_voice_name:
        payload["voice"] = resolved_voice_name
        payload.setdefault("voiceName", resolved_voice_name)
    if resolved_voice_id:
        payload.setdefault("voiceId", resolved_voice_id)
        payload.setdefault("voice_id", resolved_voice_id)
        payload.setdefault("voiceCloneId", resolved_voice_id)
        payload.setdefault("voice_clone_id", resolved_voice_id)
        payload.setdefault("cloneId", resolved_voice_id)
    if sample_rate_hz:
        payload["sample_rate"] = int(sample_rate_hz)
        payload.setdefault("audio", {})
        if isinstance(payload["audio"], dict):
            payload["audio"].setdefault("sample_rate", int(sample_rate_hz))
    payload.setdefault("audio", {}).setdefault("format", ext)
    payload.setdefault("output", {}).setdefault("format", ext)
    payload.setdefault("options", {}).setdefault("format", ext)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json, audio/mpeg, audio/wav, audio/ogg",
        "Content-Type": "application/json",
    }
    status, content, resp_headers = _http_post(endpoint, headers=headers, json_body=payload)
    if status < 200 or status >= 300:  # pragma: no cover - network path
        # Some APIs return JSON with base64 audio; attempt to parse
        try:
            err_json = json.loads(content.decode("utf-8", errors="ignore"))
        except Exception:
            err_json = {"body": content[:200].decode("utf-8", errors="ignore")}
        raise RuntimeError(f"TTS failed: {status} {err_json}")

    # Heuristic: if response is small JSON, attempt base64 decode
    ct = (resp_headers.get("Content-Type") or "").lower()
    if "application/json" in ct:  # pragma: no cover - network path
        data = json.loads(content.decode("utf-8", errors="ignore"))
        audio_bytes = _decode_audio_payload(data)
        if not audio_bytes:
            raise RuntimeError(f"TTS response missing audio payload; headers={resp_headers}")
    else:
        audio_bytes = content

    _write_bytes(file_path, audio_bytes)
    return {"messageId": message_id, "path": str(file_path), "ext": ext, "bytes": len(audio_bytes), "dry": False}


def _twilio_create_call(to_number: str, play_message_id: str, ext: str) -> Dict[str, Any]:
    account_sid = _env("TWILIO_ACCOUNT_SID")
    auth_token = _env("TWILIO_AUTH_TOKEN")
    from_number = _env("TWILIO_FROM_NUMBER")
    base_url = _env("BASE_URL")  # public URL to this app (master_server) serving TwiML/audio
    if not all([account_sid, auth_token, from_number, base_url]):
        raise RuntimeError("Missing Twilio or BASE_URL env (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, BASE_URL)")

    call_id = _new_id("call")
    twiml_url = f"{base_url}/phone/twiml?callId={call_id}&messageId={play_message_id}&ext={ext}"
    url = f"{_twilio_base_url()}/Accounts/{account_sid}/Calls.json"
    status, content, _ = _http_post(
        url,
        auth=(account_sid, auth_token),
        data={
            "To": to_number,
            "From": from_number,
            "Url": twiml_url,
            "Method": "GET",
        },
    )
    if status < 200 or status >= 300:  # pragma: no cover - network path
        raise RuntimeError(f"Twilio create call failed: {status} {content[:200]!r}")
    try:
        resp = json.loads(content.decode("utf-8"))
    except Exception:  # pragma: no cover
        resp = {"raw": content[:200].decode("utf-8", errors="ignore")}
    call_sid = resp.get("sid") or resp.get("Sid")
    return {"callId": call_id, "twilioCallSid": call_sid, "twimlUrl": twiml_url, "twilio": resp}


def _twilio_redirect_call(call_sid: str, call_id: str, play_message_id: str, ext: str) -> bool:
    account_sid = _env("TWILIO_ACCOUNT_SID")
    auth_token = _env("TWILIO_AUTH_TOKEN")
    base_url = _env("BASE_URL")
    if not all([account_sid, auth_token, base_url]):
        raise RuntimeError("Missing Twilio or BASE_URL env")
    twiml_url = f"{base_url}/phone/twiml?callId={call_id}&messageId={play_message_id}&ext={ext}"
    url = f"{_twilio_base_url()}/Accounts/{account_sid}/Calls/{call_sid}.json"
    status, content, _ = _http_post(
        url,
        auth=(account_sid, auth_token),
        data={
            "Url": twiml_url,
            "Method": "GET",
        },
    )
    return 200 <= status < 300


def _twilio_end_call(call_sid: str) -> bool:
    account_sid = _env("TWILIO_ACCOUNT_SID")
    auth_token = _env("TWILIO_AUTH_TOKEN")
    if not all([account_sid, auth_token]):
        raise RuntimeError("Missing Twilio env")
    url = f"{_twilio_base_url()}/Accounts/{account_sid}/Calls/{call_sid}.json"
    status, content, _ = _http_post(
        url, auth=(account_sid, auth_token), data={"Status": "completed"}
    )
    return 200 <= status < 300


@server.tool()
def start_call(
    phone_number: str,
    text: str,
    voice: Optional[str] = None,
    model: Optional[str] = None,
    format: str = "mp3",
    sample_rate_hz: Optional[int] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Start a phone call and play TTS output once answered.

    Returns: { callId, twilioCallSid, audio: { messageId, url, format } }
    """
    tts = synthesize_tts(text, model=model, voice=voice, fmt=format, sample_rate_hz=sample_rate_hz, dry_run=dry_run)
    message_id = tts["messageId"]
    ext = tts["ext"]

    base_url = _env("BASE_URL") or ""
    audio_url = f"{base_url}/phone/audio/{message_id}.{ext}" if base_url else None

    call = _twilio_create_call(phone_number, message_id, ext)
    return {
        "callId": call["callId"],
        "twilioCallSid": call.get("twilioCallSid"),
        "twimlUrl": call.get("twimlUrl"),
        "audio": {"messageId": message_id, "url": audio_url, "format": ext, "bytes": tts.get("bytes")},
        "dry": tts.get("dry", False),
    }


@server.tool()
def speak_text(
    call_id: str,
    twilio_call_sid: str,
    text: str,
    voice: Optional[str] = None,
    model: Optional[str] = None,
    format: str = "mp3",
    sample_rate_hz: Optional[int] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Generate a new TTS clip and redirect the live call to play it immediately."""
    tts = synthesize_tts(text, model=model, voice=voice, fmt=format, sample_rate_hz=sample_rate_hz, dry_run=dry_run)
    ok = _twilio_redirect_call(twilio_call_sid, call_id, tts["messageId"], tts["ext"])
    base_url = _env("BASE_URL") or ""
    audio_url = f"{base_url}/phone/audio/{tts['messageId']}.{tts['ext']}" if base_url else None
    return {
        "messageId": tts["messageId"],
        "url": audio_url,
        "format": tts["ext"],
        "redirected": bool(ok),
        "dry": tts.get("dry", False),
    }


@server.tool()
def end_call(twilio_call_sid: str) -> Dict[str, Any]:
    """Hang up the active call by Twilio Call SID."""
    ok = _twilio_end_call(twilio_call_sid)
    return {"success": bool(ok)}


if __name__ == "__main__":
    # Use FastMCP's built-in stdio transport runner
    import asyncio

    async def main() -> None:
        await server.run_stdio_async()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
