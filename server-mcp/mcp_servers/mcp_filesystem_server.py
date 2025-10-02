from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Dict

from mcp.server.fastmcp import FastMCP as Server


server = Server("filesystem-mcp")


def repo_root() -> Path:
  # This file: .../server-mcp/Housing-Property-Agent-MCP/mcp_servers/mcp_filesystem_server.py
  # repo root is 3 parents up: mcp_servers -> Housing-Property-Agent-MCP -> server-mcp -> repo_root
  return Path(__file__).resolve().parents[3]


def workflows_path() -> Path:
  return repo_root() / "frontend" / "Housing-Agent-Lovable" / "public" / "workflows.json"


@server.tool()
async def read_workflows() -> List[Dict[str, Any]]:
  """Read workflow entries from the public workflows.json file"""
  path = workflows_path()
  if not path.exists():
    return []
  data = json.loads(path.read_text(encoding="utf-8") or "[]")
  return data if isinstance(data, list) else []


@server.tool()
async def write_workflows(json_array: List[Dict[str, Any]]) -> Dict[str, Any]:
  """Overwrite workflows.json with the provided array"""
  path = workflows_path()
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(json_array, indent=2), encoding="utf-8")
  return {"ok": True, "count": len(json_array)}


@server.tool()
async def append_workflow_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
  """Append a single workflow entry to workflows.json in a read-modify-write manner"""
  path = workflows_path()
  path.parent.mkdir(parents=True, exist_ok=True)
  current = []
  if path.exists():
    try:
      current = json.loads(path.read_text(encoding="utf-8") or "[]")
      if not isinstance(current, list):
        current = []
    except Exception:
      current = []
  current.append(entry)
  path.write_text(json.dumps(current, indent=2), encoding="utf-8")
  return {"ok": True, "count": len(current)}


async def main() -> None:
  # Use FastMCP's built-in stdio transport runner
  await server.run_stdio_async()


if __name__ == "__main__":
  import asyncio
  asyncio.run(main())
