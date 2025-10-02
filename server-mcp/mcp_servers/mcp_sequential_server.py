from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Literal

from anthropic import Anthropic
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP as Server


server = Server("sequentialthinking-mcp")
logger = logging.getLogger(__name__)
from pathlib import Path

# Path to the current file's directory
env_path = Path(__file__).resolve().parent / ".env"

load_dotenv(dotenv_path=env_path)

ANTHROPIC_MODEL = "claude-3-7-sonnet-20250219"
_anthropic_client: Anthropic | None = None

Category = Literal["plumbing", "hvac", "electrical", "appliances", "structural", "other"]
Priority = Literal["low", "medium", "high", "urgent"]
Resp = Literal["tenant", "landlord", "shared", "unknown"]


def _basic_classify(prompt: str) -> Dict[str, str]:
  p = prompt.lower()
  if any(k in p for k in ["leak", "plumb", "water", "sink", "toilet", "faucet"]):
    category: Category = "plumbing"
  elif any(k in p for k in ["heat", "hvac", "air", "temperature"]):
    category = "hvac"
  elif any(k in p for k in ["light", "electrical", "power", "outlet"]):
    category = "electrical"
  elif any(k in p for k in ["appliance", "refrigerator", "stove", "washer", "dryer"]):
    category = "appliances"
  elif any(k in p for k in ["wall", "ceiling", "floor", "door", "window"]):
    category = "structural"
  else:
    category = "other"

  if any(k in p for k in ["urgent", "emergency", "immediately"]):
    priority: Priority = "urgent"
  elif any(k in p for k in ["high", "asap", "quickly"]):
    priority = "high"
  elif any(k in p for k in ["low", "when possible", "eventually"]):
    priority = "low"
  else:
    priority = "medium"

  if category in ("plumbing", "electrical", "hvac", "structural"):
    responsibility: Resp = "landlord"
  elif category == "appliances":
    responsibility = "shared"
  else:
    responsibility = "unknown"

  return {
    "category": category,
    "priority": priority,
    "responsibility_guess": responsibility,
    "source": "heuristic",
  }


def _get_anthropic_client() -> Anthropic | None:
  global _anthropic_client
  if _anthropic_client is not None:
    return _anthropic_client

  api_key = os.environ.get("ANTHROPIC_API_KEY")
  if not api_key:
    return None

  try:
    _anthropic_client = Anthropic(api_key=api_key)
  except Exception as exc:  # pragma: no cover - defensive path
    logger.warning("Unable to initialize Anthropic client: %s", exc)
    _anthropic_client = None
  return _anthropic_client


async def classify(prompt: str) -> Dict[str, str]:
  client = _get_anthropic_client()
  if client is None:
    return _basic_classify(prompt)

  system_instruction = (
    "You classify residential maintenance issues. "
    "Respond with pure JSON object containing keys 'category', 'priority',"
    " and 'responsibility'. Allowed category values: plumbing, hvac, electrical,"
    " appliances, structural, other. Allowed priority: low, medium, high, urgent."
    " Allowed responsibility: tenant, landlord, shared, unknown."
  )

  try:
    response = await asyncio.to_thread(
      client.messages.create,
      model=ANTHROPIC_MODEL,
      max_tokens=256,
      system=system_instruction,
      messages=[
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": (
                "Classify the following maintenance request: "
                f"{prompt.strip()}"
              ),
            }
          ],
        }
      ],
    )

    text_blocks = [
      getattr(block, "text", "")
      for block in (response.content or [])
      if getattr(block, "type", None) == "text"
    ]
    raw_text = "\n".join(chunk.strip() for chunk in text_blocks if chunk.strip())
    parsed = json.loads(raw_text)

    category = str(parsed.get("category", "other")).lower()
    priority = str(parsed.get("priority", "medium")).lower()
    responsibility = str(parsed.get("responsibility", "unknown")).lower()

    if category not in ["plumbing", "hvac", "electrical", "appliances", "structural", "other"]:
      category = "other"
    if priority not in ["low", "medium", "high", "urgent"]:
      priority = "medium"
    if responsibility not in ["tenant", "landlord", "shared", "unknown"]:
      responsibility = "unknown"

    return {
      "category": category,
      "priority": priority,
      "responsibility_guess": responsibility,
      "source": "anthropic",
    }
  except Exception as exc:
    logger.warning("Anthropic classification failed, falling back: %s", exc)
    return _basic_classify(prompt)


@server.tool()
async def plan_prompt_to_steps(prompt: str) -> List[Dict[str, str]]:
  """Break a user prompt into concrete action steps.

  Returns a list of {step, rationale} objects.
  """
  p = prompt.lower()
  steps: List[Dict[str, str]] = []

  if any(k in p for k in ["leak", "repair", "maintenance", "broken", "not working"]):
    steps = [
      {"step": "Classify maintenance issue", "rationale": "Determine category/priority/responsibility"},
      {"step": "Create maintenance ticket", "rationale": "Track the issue with tenant + unit"},
      {"step": "Append workflow entry", "rationale": "Show planned steps and results in UI"},
    ]
  elif any(k in p for k in ["rent cover", "what does my rent", "lease components"]):
    steps = [
      {"step": "Fetch rent details", "rationale": "Get base rent and included components"},
      {"step": "Summarize details", "rationale": "Return a concise breakdown"},
    ]
  elif any(k in p for k in ["who is due", "overdue", "due this week", "upcoming payments"]):
    steps = [
      {"step": "List due payments", "rationale": "Find leases due/overdue for the period"},
      {"step": "Prepare reminders", "rationale": "Optionally trigger notifications (mock)"},
    ]
  else:
    steps = [
      {"step": "Clarify intent", "rationale": "Ask user a follow-up question"}
    ]

  return steps


@server.tool()
async def classify_issue(prompt: str) -> Dict[str, str]:
  """Classify a maintenance issue from free text into {category, priority, responsibility_guess}"""
  return await classify(prompt)


async def main() -> None:
  await server.run_stdio_async()


if __name__ == "__main__":
  import asyncio
  asyncio.run(main())
