#!/bin/bash

# Example MCP requests for the Go Calculator server
# Make sure the server is running on http://localhost:8200

BASE_URL="http://localhost:8200/mcp/v1/messages"

echo "========================================="
echo "Go Calculator MCP Server - Example Requests"
echo "========================================="
echo ""

# Check if server is running
echo "1. Checking server health..."
curl -s http://localhost:8200/health | jq '.'
echo ""

# Initialize MCP session
echo "2. Initializing MCP session..."
curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "example-client",
        "version": "1.0.0"
      }
    }
  }' | jq '.'
echo ""

# List available tools
echo "3. Listing available tools..."
curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
  }' | jq '.'
echo ""

# Test add operation
echo "4. Testing add operation (5 + 3)..."
curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "add",
      "arguments": {
        "a": 5,
        "b": 3
      }
    }
  }' | jq '.'
echo ""

# Test subtract operation
echo "5. Testing subtract operation (10 - 4)..."
curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "subtract",
      "arguments": {
        "a": 10,
        "b": 4
      }
    }
  }' | jq '.'
echo ""

# Test multiply operation
echo "6. Testing multiply operation (7 * 6)..."
curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 5,
    "method": "tools/call",
    "params": {
      "name": "multiply",
      "arguments": {
        "a": 7,
        "b": 6
      }
    }
  }' | jq '.'
echo ""

# Test divide operation
echo "7. Testing divide operation (15 / 3)..."
curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 6,
    "method": "tools/call",
    "params": {
      "name": "divide",
      "arguments": {
        "a": 15,
        "b": 3
      }
    }
  }' | jq '.'
echo ""

# Test divide by zero (error case)
echo "8. Testing divide by zero (10 / 0) - should return error..."
curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 7,
    "method": "tools/call",
    "params": {
      "name": "divide",
      "arguments": {
        "a": 10,
        "b": 0
      }
    }
  }' | jq '.'
echo ""

# Test with decimal numbers
echo "9. Testing with decimals (3.14 * 2.5)..."
curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 8,
    "method": "tools/call",
    "params": {
      "name": "multiply",
      "arguments": {
        "a": 3.14,
        "b": 2.5
      }
    }
  }' | jq '.'
echo ""

# Check metrics
echo "10. Checking server metrics..."
curl -s http://localhost:8200/metrics | jq '.'
echo ""

echo "========================================="
echo "All example requests completed!"
echo "========================================="
