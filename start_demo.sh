#!/bin/bash

# Housing Agent MCP Demo Startup Script
# This script helps start the master server and frontend for testing

set -e

export NEWPORT_API_KEY=4ed1a9a571cf4ca2ba19dcdd26c33dc8

echo "🏠 Housing Agent MCP Demo Startup"
echo "================================="

# Check for server configuration file in MCP server directory
if [ ! -f "server-mcp/Housing-Property-Agent-MCP/server_config.json" ]; then
    echo "❌ Error: server-mcp/Housing-Property-Agent-MCP/server_config.json not found. Please run this script from the repo root."
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is required but not installed."
    exit 1
fi

# Check if Node.js is available
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is required but not installed."
    exit 1
fi

echo ""
echo "🔧 Step 1: Testing MCP Server Connections..."
# Use project virtualenv to ensure dependencies are available
pushd server-mcp/Housing-Property-Agent-MCP >/dev/null
if NO_LLM=1 ./.venv/bin/python ../../test_workflow_creation.py; then
    echo "✅ MCP tests passed!"
else
    echo "⚠️  MCP tests failed, but continuing with demo..."
fi
popd >/dev/null

echo ""
echo "🚀 Step 2: Starting Master Server..."
echo "   Server will run on http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""

# Start the master server in the background using the repo's virtualenv
cd server-mcp/Housing-Property-Agent-MCP
./.venv/bin/python master_server.py &
MASTER_PID=$!
cd ../..

# Wait a moment for the server to start
sleep 3

echo ""
echo "🌐 Step 3: Starting Frontend..."
echo "   Frontend will run on http://localhost:5173"
echo "   Press Ctrl+C to stop both servers"
echo ""

# Create .env.local if it doesn't exist
if [ ! -f "frontend/Housing-Agent-Lovable/.env.local" ]; then
    echo "📝 Creating .env.local file..."
    cat > frontend/Housing-Agent-Lovable/.env.local << EOF
VITE_MASTER_SERVER_BASE=http://localhost:8000
VITE_LEASE_ID=1
VITE_TENANT_EMAIL=sarah@example.com
EOF
fi

# Start the frontend
cd frontend/Housing-Agent-Lovable

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm ci
fi

# Start the dev server
npm run dev &
FRONTEND_PID=$!

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $MASTER_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo ""
echo "✅ Demo is running!"
echo "   - Master Server: http://localhost:8000"
echo "   - Frontend: http://localhost:5173"
echo "   - Try the Tenant Portal and send a chat message like:"
echo "     'My kitchen sink is leaking badly'"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
wait
