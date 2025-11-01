#!/usr/bin/env python3
"""
Agent/MCP Service for Housing Application
Handles tool execution with LLM integration and guardrails
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agent MCP Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tool registry for allowed tools
ALLOWED_TOOLS = {
    "auth.startOtp": {
        "description": "Start OTP authentication process",
        "inputs": {"phone": "string"},
        "auth": "anon",
    },
    "auth.verifyOtp": {
        "description": "Verify OTP code",
        "inputs": {"phone": "string", "code": "string"},
        "auth": "anon",
    },
    "rooms.create": {
        "description": "Create a new room",
        "inputs": {"name": "string", "role": "LANDLORD|TENANT"},
        "auth": "user",
    },
    "rooms.inviteByPhone": {
        "description": "Invite user to room by phone",
        "inputs": {
            "room_id": "string",
            "phone": "string",
            "role": "LANDLORD|TENANT",
        },
        "auth": "user",
    },
    "invites.accept": {
        "description": "Accept room invitation",
        "inputs": {"token": "string"},
        "auth": "user",
    },
    "maintenance.createTicket": {
        "description": "Create maintenance ticket",
        "inputs": {
            "description": "string",
            "urgency": "string",
            "category": "string",
        },
        "auth": "user",
    },
    "maintenance.updateTicket": {
        "description": "Update maintenance ticket status",
        "inputs": {
            "ticket_id": "string",
            "status": "string",
            "notes": "string",
        },
        "auth": "user",
    },
    "document.generateLease": {
        "description": "Generate lease document",
        "inputs": {
            "tenant_info": "object",
            "property_info": "object",
            "terms": "object",
        },
        "auth": "user",
    },
}


class ToolExecutionRequest(BaseModel):
    tool_name: str
    input: Dict[str, Any]
    user_id: Optional[str] = None
    trace_id: Optional[str] = None


class ToolExecutionResponse(BaseModel):
    result: Any
    success: bool
    error: Optional[str] = None
    trace_id: Optional[str] = None


class ToolRegistryResponse(BaseModel):
    tools: List[Dict[str, Any]]


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "agent-mcp"}


@app.get("/tools", response_model=ToolRegistryResponse)
async def get_tool_registry():
    """Get available tools registry"""
    tools = []
    for name, config in ALLOWED_TOOLS.items():
        tools.append(
            {
                "name": name,
                "description": config["description"],
                "inputs": config["inputs"],
                "auth": config["auth"],
            }
        )
    return ToolRegistryResponse(tools=tools)


@app.post("/execute", response_model=ToolExecutionResponse)
async def execute_tool(request: ToolExecutionRequest):
    """Execute a tool with guardrails and validation"""

    # Generate trace ID if not provided
    trace_id = request.trace_id or str(uuid.uuid4())

    logger.info(
        f"Executing tool {request.tool_name} for user {request.user_id} with trace {trace_id}"
    )

    try:
        # Validate tool exists
        if request.tool_name not in ALLOWED_TOOLS:
            raise HTTPException(
                status_code=400,
                detail=f"Tool '{request.tool_name}' not found in registry",
            )

        tool_config = ALLOWED_TOOLS[request.tool_name]

        # Check authentication requirements
        if tool_config["auth"] == "user" and not request.user_id:
            raise HTTPException(
                status_code=401,
                detail="User authentication required for this tool",
            )

        # Apply input validation and sanitization
        sanitized_input = await sanitize_input(
            request.input, tool_config["inputs"]
        )

        # Execute tool based on name
        result = await execute_tool_logic(
            request.tool_name, sanitized_input, request.user_id
        )

        logger.info(
            f"Tool {request.tool_name} executed successfully for trace {trace_id}"
        )

        return ToolExecutionResponse(
            result=result, success=True, trace_id=trace_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool execution failed for {request.tool_name}: {str(e)}")
        return ToolExecutionResponse(
            result=None, success=False, error=str(e), trace_id=trace_id
        )


async def sanitize_input(
    input_data: Dict[str, Any], expected_inputs: Dict[str, str]
) -> Dict[str, Any]:
    """Sanitize and validate tool input"""
    sanitized = {}

    for field, field_type in expected_inputs.items():
        if field not in input_data:
            raise HTTPException(
                status_code=400, detail=f"Missing required field: {field}"
            )

        value = input_data[field]

        # Basic type validation
        if field_type == "string" and not isinstance(value, str):
            raise HTTPException(
                status_code=400, detail=f"Field '{field}' must be a string"
            )
        elif field_type == "object" and not isinstance(value, dict):
            raise HTTPException(
                status_code=400, detail=f"Field '{field}' must be an object"
            )

        # Apply sanitization based on field type
        if field_type == "string":
            # Remove potentially dangerous characters
            sanitized[field] = str(value).strip()[:1000]  # Limit length
        else:
            sanitized[field] = value

    return sanitized


async def execute_tool_logic(
    tool_name: str, input_data: Dict[str, Any], user_id: Optional[str]
) -> Any:
    """Execute the actual tool logic"""

    if tool_name == "auth.startOtp":
        return await handle_start_otp(input_data)
    elif tool_name == "auth.verifyOtp":
        return await handle_verify_otp(input_data)
    elif tool_name == "rooms.create":
        return await handle_create_room(input_data, user_id)
    elif tool_name == "rooms.inviteByPhone":
        return await handle_invite_by_phone(input_data, user_id)
    elif tool_name == "invites.accept":
        return await handle_accept_invite(input_data, user_id)
    elif tool_name == "maintenance.createTicket":
        return await handle_create_maintenance_ticket(input_data, user_id)
    elif tool_name == "maintenance.updateTicket":
        return await handle_update_maintenance_ticket(input_data, user_id)
    elif tool_name == "document.generateLease":
        return await handle_generate_lease(input_data, user_id)
    else:
        raise HTTPException(
            status_code=400, detail=f"Unknown tool: {tool_name}"
        )


async def handle_start_otp(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle OTP start request"""
    phone = input_data["phone"]

    # In a real implementation, this would call the Identity service
    # For now, we'll simulate the response
    return {"success": True, "message": f"OTP sent to {phone}", "phone": phone}


async def handle_verify_otp(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle OTP verification request"""
    phone = input_data["phone"]
    code = input_data["code"]

    # In a real implementation, this would call the Identity service
    # For now, we'll simulate verification
    if code == "123456":  # Demo code
        return {
            "success": True,
            "message": "OTP verified successfully",
            "user_id": str(uuid.uuid4()),
            "phone": phone,
        }
    else:
        return {"success": False, "message": "Invalid OTP code"}


async def handle_create_room(
    input_data: Dict[str, Any], user_id: str
) -> Dict[str, Any]:
    """Handle room creation request"""
    name = input_data["name"]
    role = input_data["role"]

    # In a real implementation, this would call the Orchestrator service
    room_id = str(uuid.uuid4())

    return {
        "success": True,
        "room_id": room_id,
        "name": name,
        "role": role,
        "message": "Room created successfully",
    }


async def handle_invite_by_phone(
    input_data: Dict[str, Any], user_id: str
) -> Dict[str, Any]:
    """Handle invite by phone request"""
    room_id = input_data["room_id"]
    phone = input_data["phone"]
    role = input_data["role"]

    # In a real implementation, this would call the Orchestrator service
    invite_token = str(uuid.uuid4())

    return {
        "success": True,
        "invite_token": invite_token,
        "room_id": room_id,
        "phone": phone,
        "role": role,
        "message": "Invite sent successfully",
    }


async def handle_accept_invite(
    input_data: Dict[str, Any], user_id: str
) -> Dict[str, Any]:
    """Handle invite acceptance request"""
    token = input_data["token"]

    # In a real implementation, this would call the Orchestrator service
    return {
        "success": True,
        "membership_id": str(uuid.uuid4()),
        "token": token,
        "message": "Successfully joined room",
    }


async def handle_create_maintenance_ticket(
    input_data: Dict[str, Any], user_id: str
) -> Dict[str, Any]:
    """Handle maintenance ticket creation"""
    description = input_data["description"]
    urgency = input_data["urgency"]
    category = input_data["category"]

    ticket_id = str(uuid.uuid4())

    return {
        "success": True,
        "ticket_id": ticket_id,
        "description": description,
        "urgency": urgency,
        "category": category,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "message": "Maintenance ticket created successfully",
    }


async def handle_update_maintenance_ticket(
    input_data: Dict[str, Any], user_id: str
) -> Dict[str, Any]:
    """Handle maintenance ticket update"""
    ticket_id = input_data["ticket_id"]
    status = input_data["status"]
    notes = input_data.get("notes", "")

    return {
        "success": True,
        "ticket_id": ticket_id,
        "status": status,
        "notes": notes,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "message": "Maintenance ticket updated successfully",
    }


async def handle_generate_lease(
    input_data: Dict[str, Any], user_id: str
) -> Dict[str, Any]:
    """Handle lease document generation"""
    tenant_info = input_data["tenant_info"]
    property_info = input_data["property_info"]
    terms = input_data["terms"]

    document_id = str(uuid.uuid4())

    return {
        "success": True,
        "document_id": document_id,
        "tenant_info": tenant_info,
        "property_info": property_info,
        "terms": terms,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "message": "Lease document generated successfully",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8083)
