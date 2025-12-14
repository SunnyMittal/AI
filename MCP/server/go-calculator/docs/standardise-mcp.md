# Standardize Go MCP Server to FastMCP Protocol

## Overview

This document describes the changes made to align the Go calculator MCP server with the FastMCP streamable-http standard, enabling seamless switching between Python and Go server implementations.

## Changes Made

### 1. Protocol Version Update

**File:** `internal/mcp/protocol.go`

- Added `ProtocolVersion` constant: `2025-03-26` (FastMCP compatible)
- Added HTTP header constants:
  - `HeaderMCPSessionID = "mcp-session-id"`
  - `HeaderMCPProtocolVersion = "mcp-protocol-version"`

### 2. Unified `/mcp` Endpoint

**File:** `internal/mcp/transport.go`

Previous endpoints:
- `/mcp/v1/messages` (POST)
- `/mcp/v1/sse` (GET)

New endpoint:
- `/mcp` (GET, POST, DELETE)

HTTP methods:
- **POST** - Send JSON-RPC requests, receive SSE response
- **GET** - Establish SSE stream for server-initiated messages
- **DELETE** - Terminate session

### 3. Session Management

Added session tracking with `mcp-session-id` header:
- Sessions are created on first `initialize` request
- Session ID returned in response headers
- Subsequent requests must include valid session ID
- Sessions can be terminated via DELETE request

### 4. SSE Response Format

All POST responses now use SSE format:
```
event: message
data: {"jsonrpc":"2.0","id":1,"result":{...}}

```

Headers:
- `Content-Type: text/event-stream`
- `Cache-Control: no-cache, no-transform`
- `mcp-session-id: <session-id>`

### 5. Accept Header Validation

POST requests must include `Accept: text/event-stream` or `Accept: */*`
Returns 406 Not Acceptable if missing.

## Client Configuration

To use the Go server, set in client `.env`:
```
MCP_SERVER_URL=http://127.0.0.1:8000/mcp
```

Both Python and Go servers now use the same endpoint format.

## Testing

1. Start the Go server:
   ```bash
   cd D:\AI\MCP\server\go-calculator
   go run ./cmd/server
   ```

2. The client should connect without any code changes (just update the URL).

## Protocol Compatibility

| Feature | Python (FastMCP) | Go Server |
|---------|------------------|-----------|
| Endpoint | `/mcp` | `/mcp` |
| Response format | SSE | SSE |
| Session management | `mcp-session-id` | `mcp-session-id` |
| Protocol version | `2025-03-26` | `2025-03-26` |
