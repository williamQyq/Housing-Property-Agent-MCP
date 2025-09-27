#!/usr/bin/env python3
"""
Simple test script to verify MCP server connections and workflow creation.
Run this from the repo root to test the master server functionality.
"""

import asyncio
import json
import os
import sqlite3
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

# Add the master server directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "server-mcp" / "Housing-Property-Agent-MCP"))

import httpx

from master_server import MCPMaster, app


@asynccontextmanager
async def lifespan_context(app_obj):
    manager = app_obj.router.lifespan_context(app_obj)
    await manager.__aenter__()
    try:
        yield
    finally:
        await manager.__aexit__(None, None, None)


async def test_mcp_connections():
    """Test MCP server connections and tool availability."""
    print("🔧 Testing MCP Server Connections...")
    
    master = MCPMaster()
    try:
        await master.connect_to_servers()
        
        print(f"✅ Connected to {len(master.sessions)} MCP servers")
        print(f"✅ Available tools: {[tool['name'] for tool in master.available_tools]}")
        
        # Test specific tools we need
        required_tools = ['classify_issue', 'create_maintenance_ticket', 'append_workflow_entry', 'list_tickets']
        missing_tools = [tool for tool in required_tools if tool not in master.tool_to_session]
        
        if missing_tools:
            print(f"❌ Missing required tools: {missing_tools}")
            return False
        else:
            print("✅ All required tools are available")
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to MCP servers: {e}")
        return False
    finally:
        await master.cleanup()


async def test_workflow_creation():
    """
    {
    "id": "validation-test",
    "createdAt": "2024-01-01T12:00:00Z",
    "prompt": "Validation test workflow",
    "steps": [
      {
        "title": "Classify maintenance issue",
        "status": "done"
      },
      {
        "title": "Create maintenance ticket",
        "status": "done",
        "note": "ticket_id=999"
      },
    ],
    "result": {
      "type": "ticket",
      "data": {
        "ticket_id": 999,
        "category": "test",
        "priority": "medium"
      }
    }
  }
    :return:
    """
    """Test workflow creation with a sample maintenance request."""
    print("\n🔄 Testing Workflow Creation...")
    
    # In restricted environments, allow disabling LLM path
    if os.environ.get("NO_LLM") == "1":
        os.environ.pop("ANTHROPIC_API_KEY", None)

    master = MCPMaster()
    try:
        await master.connect_to_servers()
        
        # Test with a sample maintenance prompt
        test_prompt = "My kitchen faucet is leaking badly and water is pooling on the floor"
        print(f"📝 Testing with prompt: '{test_prompt}'")
        
        result = await master.process_query(test_prompt)
        print(f"✅ Master server response: {result.get('text', 'No text response')[:100]}...")
        
        # Check if workflow was created
        workflows_path = Path(__file__).parent / "frontend" / "Housing-Agent-Lovable" / "public" / "workflows.json"
        if workflows_path.exists():
            with open(workflows_path, 'r') as f:
                workflows = json.load(f)
            print(f"✅ Workflows file exists with {len(workflows)} entries")
            if workflows:
                latest = workflows[-1]
                print(f"✅ Latest workflow: {latest.get('prompt', 'No prompt')[:50]}...")
                print(f"✅ Steps: {len(latest.get('steps', []))} steps")
        else:
            print("❌ Workflows file not found")
            
        return True
        
    except Exception as e:
        print(f"❌ Workflow creation test failed: {e}")
        return False
    finally:
        await master.cleanup()


async def test_chat_creates_ticket():
    """Ensure /chat inserts a maintenance ticket for lease_id=1 when prompted."""
    print("\n🧪 Testing /chat maintenance ticket creation...")

    db_path = Path(__file__).parent / "server-mcp" / "Housing-Property-Agent-MCP" / "data" / "app.db"

    def ticket_count() -> int:
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM maintenance_tickets WHERE lease_id = 1"
            )
            row = cursor.fetchone()
            return int(row[0]) if row else 0

    # Ensure LLM branch runs (we will patch the Anthropic call itself).
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
    if os.environ.get("NO_LLM") == "1":
        os.environ.pop("NO_LLM")

    prompt = "My kitchen faucet is leaking badly and I need urgent help"

    before = ticket_count()

    class FakeAnthropicSequence:
        def __init__(self) -> None:
            self.calls = 0

        def next_response(self) -> SimpleNamespace:
            self.calls += 1
            if self.calls == 1:
                # First turn: request the maintenance ticket tool.
                return SimpleNamespace(
                    content=[
                        SimpleNamespace(
                            type="tool_use",
                            id="tool-create-ticket",
                            name="create_maintenance_ticket",
                            input={
                                "issue": prompt,
                                "lease_id": 1,
                                "category": "plumbing",
                                "priority": "urgent",
                                "responsibility_guess": "landlord",
                            },
                        )
                    ]
                )
            # Subsequent turns: return plain text completion.
            return SimpleNamespace(
                content=[
                    SimpleNamespace(
                        type="text",
                        text="Created a maintenance ticket and notified the landlord.",
                    )
                ]
            )

    sequence = FakeAnthropicSequence()

    async def fake_anthropic_call(self, **kwargs):  # type: ignore[override]
        return sequence.next_response()

    async with lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            with patch.object(MCPMaster, "_anthropic_call", new=fake_anthropic_call):
                response = await client.post("/chat", json={"prompt": prompt})

    response.raise_for_status()

    after = ticket_count()
    if after == before + 1:
        print(
            f"✅ Maintenance tickets for lease_id=1 increased from {before} to {after}"
        )
        return True

    print(
        f"❌ Expected ticket count to increase by 1 (before={before}, after={after})"
    )
    return False


async def test_sqlite_data():
    """Test SQLite data retrieval for lease_id=1."""
    print("\n📊 Testing SQLite Data Retrieval...")
    
    master = MCPMaster()
    try:
        await master.connect_to_servers()
        
        # Test list_tickets for lease_id=1
        session = master.tool_to_session.get('list_tickets')
        if not session:
            print("❌ list_tickets tool not available")
            return False
            
        result = await session.call_tool('list_tickets', arguments={'lease_id': 1})
        print(f"✅ Retrieved tickets for lease_id=1")
        
        # Parse the result
        items = []
        for content in result.content:
            if hasattr(content, 'text'):
                try:
                    parsed = json.loads(content.text)
                    if isinstance(parsed, list):
                        items.extend(parsed)
                except:
                    pass
        
        print(f"✅ Found {len(items)} maintenance tickets for lease_id=1")
        for item in items[:3]:  # Show first 3
            print(f"   - {item.get('issue', 'No description')[:50]}...")
            
        return True
        
    except Exception as e:
        print(f"❌ SQLite data test failed: {e}")
        return False
    finally:
        await master.cleanup()


async def main():
    """Run all tests."""
    print("🚀 Starting MCP Housing Agent Tests\n")
    
    # Test 1: MCP Connections
    connections_ok = await test_mcp_connections()
    
    # Test 2: SQLite Data
    sqlite_ok = await test_sqlite_data()
    
    # Test 3: Workflow Creation (only if connections work)
    workflow_ok = False
    if connections_ok:
        workflow_ok = await test_workflow_creation()

    # Test 4: /chat ticket creation (requires previous tests so tools + DB are ready)
    chat_ticket_ok = False
    if connections_ok:
        chat_ticket_ok = await test_chat_creates_ticket()

    # Summary
    print("\n📋 Test Summary:")
    print(f"   MCP Connections: {'✅' if connections_ok else '❌'}")
    print(f"   SQLite Data: {'✅' if sqlite_ok else '❌'}")
    print(f"   Workflow Creation: {'✅' if workflow_ok else '❌'}")
    print(f"   /chat Ticket Creation: {'✅' if chat_ticket_ok else '❌'}")

    if connections_ok and sqlite_ok and workflow_ok and chat_ticket_ok:
        print("\n🎉 All tests passed! The system should work correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

    return connections_ok and sqlite_ok and workflow_ok and chat_ticket_ok


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
