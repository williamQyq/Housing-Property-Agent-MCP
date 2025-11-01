"""Tests for the agent-mcp service."""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "agent-mcp"}


def test_get_tools():
    """Test tools registry endpoint."""
    response = client.get("/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) > 0

    # Check that all tools have required fields
    for tool in data["tools"]:
        assert "name" in tool
        assert "description" in tool
        assert "inputs" in tool
        assert "auth" in tool


def test_execute_tool_invalid_tool():
    """Test tool execution with invalid tool name."""
    response = client.post(
        "/execute",
        json={"tool_name": "invalid_tool", "input": {}, "user_id": "test_user"},
    )
    assert response.status_code == 400
    assert "not found in registry" in response.json()["detail"]


def test_execute_tool_missing_user_id():
    """Test tool execution without user_id for user-required tool."""
    response = client.post(
        "/execute",
        json={
            "tool_name": "rooms.create",
            "input": {"name": "Test Room", "role": "TENANT"},
        },
    )
    assert response.status_code == 401
    assert "User authentication required" in response.json()["detail"]


def test_execute_tool_missing_input():
    """Test tool execution with missing required input."""
    response = client.post(
        "/execute",
        json={
            "tool_name": "auth.startOtp",
            "input": {},
            "user_id": "test_user",
        },
    )
    assert response.status_code == 400
    assert "Missing required field" in response.json()["detail"]


def test_execute_tool_auth_start_otp():
    """Test OTP start tool execution."""
    response = client.post(
        "/execute",
        json={
            "tool_name": "auth.startOtp",
            "input": {"phone": "+1234567890"},
            "user_id": "test_user",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "OTP sent to" in data["result"]["message"]


def test_execute_tool_auth_verify_otp():
    """Test OTP verify tool execution."""
    response = client.post(
        "/execute",
        json={
            "tool_name": "auth.verifyOtp",
            "input": {"phone": "+1234567890", "code": "123456"},
            "user_id": "test_user",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "OTP verified successfully" in data["result"]["message"]


def test_execute_tool_rooms_create():
    """Test room creation tool execution."""
    response = client.post(
        "/execute",
        json={
            "tool_name": "rooms.create",
            "input": {"name": "Test Room", "role": "TENANT"},
            "user_id": "test_user",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Room created successfully" in data["result"]["message"]
    assert "room_id" in data["result"]


def test_execute_tool_maintenance_create():
    """Test maintenance ticket creation tool execution."""
    response = client.post(
        "/execute",
        json={
            "tool_name": "maintenance.createTicket",
            "input": {
                "description": "Broken faucet",
                "urgency": "medium",
                "category": "plumbing",
            },
            "user_id": "test_user",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert (
        "Maintenance ticket created successfully" in data["result"]["message"]
    )
    assert "ticket_id" in data["result"]


if __name__ == "__main__":
    pytest.main([__file__])
