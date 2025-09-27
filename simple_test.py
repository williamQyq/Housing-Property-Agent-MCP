#!/usr/bin/env python3
"""Simple test to verify workflow creation works."""

import json
import asyncio
from pathlib import Path

# Test the filesystem MCP server directly
async def test_filesystem_mcp():
    """Test filesystem MCP server workflow creation."""
    print("Testing filesystem MCP server...")
    
    # Import the filesystem server
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "server-mcp" / "Housing-Property-Agent-MCP" / "mcp_servers"))
    
    from mcp_filesystem_server import append_workflow_entry, workflows_path
    
    # Test workflow entry
    test_entry = {
        "id": "test-123",
        "createdAt": "2024-01-01T12:00:00Z",
        "prompt": "Test maintenance request",
        "steps": [
            {"title": "Classify maintenance issue", "status": "done"},
            {"title": "Create maintenance ticket", "status": "done", "note": "ticket_id=42"},
            {"title": "Contact landlord", "status": "planned"},
            {"title": "Schedule phone call for service", "status": "planned"}
        ],
        "result": {"type": "ticket", "data": {"ticket_id": 42, "category": "plumbing", "priority": "high"}}
    }
    
    try:
        # Test the workflow path resolution
        path = workflows_path()
        print(f"Workflows path: {path}")
        print(f"Path exists: {path.exists()}")
        print(f"Parent exists: {path.parent.exists()}")
        
        # Test appending workflow entry
        result = await append_workflow_entry(test_entry)
        print(f"Append result: {result}")
        
        # Verify the file was created/updated
        if path.exists():
            with open(path, 'r') as f:
                workflows = json.load(f)
            print(f"Workflows in file: {len(workflows)}")
            if workflows:
                print(f"Latest entry: {workflows[-1]['id']}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_filesystem_mcp())
    print(f"Test {'PASSED' if success else 'FAILED'}")