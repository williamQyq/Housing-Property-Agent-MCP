from __future__ import annotations

import asyncio
import json
import logging
import uuid
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from anthropic import Anthropic

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
import os

logger = logging.getLogger(__name__)

load_dotenv()


class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict


class MCPMaster:
    def __init__(self) -> None:
        self.exit_stack = AsyncExitStack()
        self.sessions: List[ClientSession] = []
        self.anthropic = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        try:
            params = StdioServerParameters(**server_config)
            transport = await self.exit_stack.enter_async_context(stdio_client(params))
            read, write = transport
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self.sessions.append(session)

            response = await session.list_tools()
            tools = response.tools
            for tool in tools:
                self.tool_to_session[tool.name] = session
                self.available_tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                )
        except Exception as e:  # pragma: no cover - startup diagnostics
            raise RuntimeError(f"Failed to connect to {server_name}: {e}") from e

    async def connect_to_servers(self) -> None:
        try:
            from pathlib import Path

            cfg_path = Path(__file__).resolve().parents[0] / "server_config.json"
            with open(cfg_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            servers = data.get("mcpServers", {})
            base_dir = cfg_path.parent
            for server_name, server_config in servers.items():
                # Normalize command and args to absolute paths relative to server config directory
                cfg = dict(server_config)
                cmd = cfg.get("command")
                if cmd and not os.path.isabs(cmd):
                    cfg["command"] = str((base_dir / cmd).resolve())
                args = cfg.get("args", []) or []
                new_args: List[str] = []
                for a in args:
                    if isinstance(a, str) and not os.path.isabs(a) and not a.startswith("-"):
                        new_args.append(str((base_dir / a).resolve()))
                    else:
                        new_args.append(a)
                cfg["args"] = new_args
                await self.connect_to_server(server_name, cfg)
        except Exception as e:
            raise RuntimeError(f"Error loading server configuration: {e}") from e

    async def _anthropic_call(self, *, max_tokens: int, model: str, tools: Any, messages: Any,
                              system: str | None = None):
        # Run the blocking SDK call in a thread to avoid blocking the event loop
        return await asyncio.to_thread(
            self.anthropic.messages.create,
            max_tokens=max_tokens,
            model=model,
            tools=tools,
            messages=messages,
            system=system
        )

    async def _call_tool_json(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        session = self.tool_to_session.get(tool_name)
        if session is None:
            raise RuntimeError(f"{tool_name} tool unavailable")

        result = await session.call_tool(tool_name, arguments=arguments or {})
        if result.structuredContent is not None:
            return result.structuredContent

        payloads: List[Any] = []
        for block in result.content or []:
            text_val = getattr(block, "text", None)
            if isinstance(text_val, str):
                try:
                    payloads.append(json.loads(text_val))
                    continue
                except Exception:
                    payloads.append(text_val)
                    continue
            if isinstance(block, dict):
                payloads.append(block)
        if not payloads:
            return None
        if len(payloads) == 1:
            return payloads[0]
        return payloads

    # --- Helper for safer tool calls ---
    async def _safe_tool_call(self, tool: str, payload: Dict[str, Any], log_error: bool = False) -> Optional[Any]:
        try:
            return await self._call_tool_json(tool, payload)
        except Exception as exc:
            log_func = logger.error if log_error else logger.warning
            log_func("Tool call %s failed: %s", tool, exc)
            return None

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a query into workflow entry, classification, and LLM-driven response."""

        # --- Step 1: Generate plan steps ---
        plan_steps_raw = await self._safe_tool_call("plan_prompt_to_steps", {"prompt": query})
        plan_steps_data = plan_steps_raw if isinstance(plan_steps_raw, list) else []
        if not plan_steps_data:
            plan_steps_data = [
                {
                    "step": "Review maintenance request",
                    "rationale": "Fallback when planner is unavailable",
                },
                {
                    "step": "Draft response for tenant",
                    "rationale": "Fallback guidance for tenant",
                },
            ]

        # --- Step 2: Classification ---
        classification_raw = await self._safe_tool_call("classify_issue", {"prompt": query})
        classification: Dict[str, Any] = classification_raw if isinstance(classification_raw, dict) else {}

        # --- Step 3: Workflow steps ---
        workflow_steps: List[Dict[str, Any]] = []
        for idx, step in enumerate(plan_steps_data):
            title = str(step.get("step") or step.get("title") or f"Step {idx + 1}")
            note = step.get("rationale") or step.get("note")
            status = "done" if idx < 2 else "planned"
            entry = {"title": title, "status": status}
            if note:
                entry["note"] = note
            workflow_steps.append(entry)

        if not workflow_steps:
            workflow_steps = [
                {"title": "Review maintenance request", "status": "done"},
                {"title": "Draft response for tenant", "status": "planned"},
            ]

        # --- Step 4: Build workflow entry ---
        workflow_entry: Dict[str, Any] = {
            "id": uuid.uuid4().hex,
            "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "prompt": query,
            "steps": workflow_steps,
            "result": {
                "type": "plan",
                "data": {
                    "category": classification.get("category", "other"),
                    "priority": classification.get("priority", "medium"),
                    "responsibility": classification.get("responsibility_guess", "unknown"),
                    "stepCount": len(workflow_steps),
                    "source": classification.get("source", "unknown"),
                },
            },
        }

        # --- Step 5: Append workflow (best-effort) ---
        workflow_append_result = await self._safe_tool_call(
            "append_workflow_entry", {"entry": workflow_entry}, log_error=True
        )

        # --- Step 6: Ask LLM to respond (preferred) ---
        anthropic_enabled = (
                bool(os.environ.get("ANTHROPIC_API_KEY")) and os.environ.get("NO_LLM") != "1"
        )

        system_message = (
            "You are an MCP-enabled assistant for a landlord–tenant maintenance app. "
            "Explain the planned actions clearly, reference the workflow ID when useful, "
            "and provide immediate guidance for tenant or landlord if applicable."
            "create maintenance ticket if tenant request medium to urgent repair, otherwise "
            "dont create ticket, only provide guidance."
        )
        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "query": query,
                            "workflowId": workflow_entry["id"],
                            "classification": classification,
                            "steps": workflow_steps,
                        },
                        indent=2,
                    ),
                }
            ],
        }

        final_text = ""
        llm_summary = False

        if anthropic_enabled:
            try:
                messages: List[Dict[str, Any]] = [user_message]
                response = await self._anthropic_call(
                    max_tokens=600,
                    model="claude-3-7-sonnet-20250219",
                    tools=self.available_tools,
                    system=system_message,
                    messages=messages,
                )

                process_query = True
                while process_query:
                    assistant_blocks: List[Dict[str, Any]] = []
                    text_blocks: List[str] = []
                    tool_block: Optional[Dict[str, Any]] = None

                    for block in response.content:
                        block_type = getattr(block, "type", None)
                        if block_type == "text":
                            text_val = getattr(block, "text", "") or ""
                            assistant_blocks.append({"type": "text", "text": text_val})
                            cleaned = text_val.strip()
                            if cleaned:
                                text_blocks.append(cleaned)
                        elif block_type == "tool_use":
                            tool_block = {
                                "type": "tool_use",
                                "id": getattr(block, "id", ""),
                                "name": getattr(block, "name", ""),
                                "input": getattr(block, "input", {}) or {},
                            }
                            assistant_blocks.append(tool_block)
                            break

                    if tool_block is None:
                        if assistant_blocks:
                            messages.append({"role": "assistant", "content": assistant_blocks})
                        if text_blocks:
                            final_text = "\n\n".join(text_blocks)
                            llm_summary = True
                        process_query = False
                        continue

                    messages.append({"role": "assistant", "content": assistant_blocks})
                    tool_id = tool_block.get("id") or ""
                    tool_name = tool_block.get("name") or ""
                    tool_args = tool_block.get("input") or {}

                    try:
                        tool_result_payload = await self._call_tool_json(tool_name, tool_args)
                    except Exception as exc:
                        tool_result_payload = {"error": str(exc)}

                    if isinstance(tool_result_payload, str):
                        result_text = tool_result_payload
                    else:
                        result_text = json.dumps(tool_result_payload, ensure_ascii=False)

                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": result_text,
                                        }
                                    ],
                                }
                            ],
                        }
                    )

                    response = await self._anthropic_call(
                        max_tokens=600,
                        model="claude-3-7-sonnet-20250219",
                        tools=self.available_tools,
                        system=system_message,
                        messages=messages,
                    )

            except Exception as exc:
                logger.warning("Anthropic call failed, fallback: %s", exc)

        # --- Step 7: Fallback if no LLM text ---
        if not final_text:
            final_text = (
                f"Recorded workflow {workflow_entry['id']} with {len(workflow_steps)} steps. "
                f"Classification: {classification.get('category', 'other')} / "
                f"Priority: {classification.get('priority', 'medium')}."
            )

        return {
            "text": final_text,
            "workflow": workflow_entry,
            "workflowUpdate": workflow_append_result,
            "classification": classification,
            "llm": {"summary": llm_summary},
        }

    async def cleanup(self) -> None:
        await self.exit_stack.aclose()


@asynccontextmanager
async def lifespan(app: FastAPI):
    master = MCPMaster()
    try:
        await master.connect_to_servers()
    except Exception as e:
        # Log and continue so the API can still start (read endpoints may fail with 500 until tools are available)
        print(f"[startup] Warning: MCP servers not connected: {e}")
    app.state.master = master
    try:
        yield
    finally:
        await master.cleanup()


app = FastAPI(title="Housing MCP Master Server", lifespan=lifespan)

# Permissive CORS for local dev; tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(TypedDict, total=False):
    prompt: str
    tenantEmail: Optional[str]
    leaseId: Optional[int]
    meta: Dict[str, Any]


class TTSRequest(TypedDict, total=False):
    text: str
    format: str
    voice: Optional[str]
    voiceId: Optional[str]
    voice_id: Optional[str]
    voiceName: Optional[str]
    voice_name: Optional[str]
    voiceCloneId: Optional[str]
    voice_clone_id: Optional[str]
    model: Optional[str]
    sample_rate_hz: Optional[int]
    dry_run: Optional[bool]


@app.post("/chat")
async def chat_endpoint(body: ChatRequest, request: Request) -> Dict[str, Any]:
    prompt = (body or {}).get("prompt")
    if not prompt or not isinstance(prompt, str):
        raise HTTPException(status_code=400, detail="Missing 'prompt' string")

    try:
        master: MCPMaster = request.app.state.master
        # Return the LLM/tool-orchestrated response directly without extra templating.
        return await master.process_query(prompt)
    except Exception as e:  # pragma: no cover - runtime error path
        raise HTTPException(status_code=500, detail=str(e))


def _sse(data: Dict[str, Any]) -> str:
    try:
        return f"data: {json.dumps(data)}\n\n"
    except Exception:
        # best-effort stringify
        return f"data: {json.dumps({'type': 'error', 'message': 'serialization error'})}\n\n"


@app.post("/chat/stream")
async def chat_stream(body: ChatRequest, request: Request) -> StreamingResponse:
    prompt = (body or {}).get("prompt")
    if not prompt or not isinstance(prompt, str):
        raise HTTPException(status_code=400, detail="Missing 'prompt' string")

    master: MCPMaster = request.app.state.master

    async def gen():
        try:
            result = await master.process_query(prompt)
            # Stream a single text event with the LLM's response
            if isinstance(result, dict):
                text = str(result.get("text") or "").strip()
            else:
                text = str(result)
            # If no text available, send the whole object as JSON
            if not text:
                text = json.dumps(result)
            yield _sse({"type": "text", "message": text})
        except Exception as e:
            yield _sse({"type": "error", "message": str(e)})
        finally:
            yield _sse({"type": "end"})

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/tenant/requests")
async def tenant_requests(
        tenantEmail: Optional[str] = None,
        tenantId: Optional[int] = None,
        leaseId: Optional[int] = None,
        limit: Optional[int] = 20,
        request: Request = None,
) -> Dict[str, Any]:
    if not tenantEmail and tenantId is None and leaseId is None:
        raise HTTPException(status_code=400, detail="tenantEmail or tenantId or leaseId is required")
    master: MCPMaster = request.app.state.master
    session = master.tool_to_session.get("list_tickets")
    if session is None:
        raise HTTPException(status_code=500, detail="list_tickets tool unavailable")
    try:
        args: Dict[str, Any] = {}
        if tenantEmail:
            args["tenant_email"] = tenantEmail
        if tenantId is not None:
            args["tenant_id"] = int(tenantId)
        if leaseId is not None:
            args["lease_id"] = int(leaseId)
        result = await session.call_tool("list_tickets", arguments=args)
        items_raw = result.content or []
        items: List[Dict[str, Any]] = []
        for entry in items_raw:
            # Handle MCP text content objects
            try:
                txt = getattr(entry, "text", None)
                if isinstance(txt, str):
                    parsed = json.loads(txt)
                    if isinstance(parsed, list):
                        items.extend([x for x in parsed if isinstance(x, dict)])
                        continue
                    if isinstance(parsed, dict):
                        items.append(parsed)
                        continue
            except Exception:
                pass
            if isinstance(entry, dict):
                items.append(entry)
            elif isinstance(entry, str):
                try:
                    parsed = json.loads(entry)
                    if isinstance(parsed, list):
                        items.extend([x for x in parsed if isinstance(x, dict)])
                except Exception:
                    pass
        requests = []
        for r in items[: (limit or 20)]:
            requests.append({
                "id": f"REQ{r.get('id')}",
                "description": r.get("issue", ""),
                "urgency": r.get("priority", "medium"),
                "category": r.get("category", "other"),
                "status": r.get("status", "open"),
                "date": str(r.get("created_at", ""))[:10],
            })
        return {"items": requests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/landlord/requests")
async def landlord_requests(limit: Optional[int] = 50, request: Request = None) -> Dict[str, Any]:
    master: MCPMaster = request.app.state.master
    session = master.tool_to_session.get("list_all_tickets")
    if session is None:
        raise HTTPException(status_code=500, detail="list_all_tickets tool unavailable")
    try:
        result = await session.call_tool("list_all_tickets", arguments={"limit": limit or 50})
        items_raw = result.content or []
        items: List[Dict[str, Any]] = []
        for entry in items_raw:
            # Handle MCP text content objects
            try:
                txt = getattr(entry, "text", None)
                if isinstance(txt, str):
                    parsed = json.loads(txt)
                    if isinstance(parsed, list):
                        items.extend([x for x in parsed if isinstance(x, dict)])
                        continue
                    if isinstance(parsed, dict):
                        items.append(parsed)
                        continue
            except Exception:
                pass
            if isinstance(entry, dict):
                items.append(entry)
            elif isinstance(entry, str):
                try:
                    parsed = json.loads(entry)
                    if isinstance(parsed, list):
                        items.extend([x for x in parsed if isinstance(x, dict)])
                except Exception:
                    pass
        requests = []
        for r in items:
            requests.append({
                "id": f"REQ{r.get('id')}",
                "tenant": r.get("tenant", ""),
                "description": r.get("issue", ""),
                "urgency": r.get("priority", "medium"),
                "category": r.get("category", "other"),
                "status": r.get("status", "open"),
                "date": str(r.get("created_at", ""))[:10],
            })
        return {"items": requests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Minimal endpoints to support Twilio + Newport TTS playback
@app.get("/phone/twiml")
async def phone_twiml(callId: str, messageId: str, ext: str = "mp3") -> Response:
    """Return TwiML instructing Twilio to play the generated audio file.

    Example: /phone/twiml?callId=call_xxx&messageId=msg_xxx&ext=mp3
    """
    audio_url = f"/phone/audio/{messageId}.{ext}"
    # For Twilio, a fully qualified URL is recommended, but Twilio will resolve relative URLs
    # against the URL used to fetch this TwiML. Ensure BASE_URL env points here in the MCP tool.
    xml = f"""
    <Response>
      <Play>{audio_url}</Play>
    </Response>
    """.strip()
    return Response(content=xml, media_type="text/xml")


@app.get("/phone/audio/{filename}")
async def phone_audio(filename: str) -> FileResponse:
    from pathlib import Path
    base = Path(__file__).resolve().parents[0] / "data" / "phone_audio"
    path = base / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="audio not found")
    # Let FileResponse set an appropriate Content-Type based on suffix
    return FileResponse(str(path))


def _audio_media_type(ext: str) -> str:
    e = (ext or "").lower().strip()
    if e == "mp3":
        return "audio/mpeg"
    if e == "wav":
        return "audio/wav"
    if e == "ogg":
        return "audio/ogg"
    return "application/octet-stream"


@app.post("/tts")
async def tts_endpoint(body: TTSRequest) -> StreamingResponse:
    """Synthesize speech for provided text using NewportAI TTS and return audio bytes.

    Body: { text: string, format?: 'mp3'|'wav'|'ogg', voice?: string, model?: string, sample_rate_hz?: number, dry_run?: boolean }
    """
    text = (body or {}).get("text")
    if not text or not isinstance(text, str):
        raise HTTPException(status_code=400, detail="Missing 'text' string")
    fmt = (body or {}).get("format") or "mp3"
    voice = (body or {}).get("voice")
    voice_id = (body or {}).get("voiceId") or (body or {}).get("voice_id")
    voice_name = (body or {}).get("voiceName") or (body or {}).get("voice_name")
    voice_clone_id = (body or {}).get("voiceCloneId") or (body or {}).get("voice_clone_id")
    model = (body or {}).get("model")
    sample_rate_hz = (body or {}).get("sample_rate_hz")
    dry_run = bool((body or {}).get("dry_run") or False)

    # Reuse the synthesize_tts from the phone-tts MCP server implementation
    try:
        from mcp_servers.mcp_phone_tts_server import synthesize_tts  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS module import failed: {e}")

    try:
        meta = await asyncio.to_thread(
            synthesize_tts,
            text,
            model=model,
            voice=voice,
            voice_id=voice_id,
            voice_name=voice_name,
            voice_clone_id=voice_clone_id,
            fmt=fmt,
            sample_rate_hz=sample_rate_hz,
            dry_run=dry_run,
        )
        from pathlib import Path
        file_path = Path(meta.get("path"))
        if not file_path.exists():
            raise RuntimeError("TTS output file missing")
        # Stream file bytes as response
        data = file_path.read_bytes()
        media_type = _audio_media_type(meta.get("ext") or fmt)
        return StreamingResponse(iter([data]), media_type=media_type)
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        # Surface the original error so clients can debug configuration issues
        raise HTTPException(status_code=502, detail=f"TTS synthesis failed: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("master_server:app", host="0.0.0.0", port=8000, reload=False)
