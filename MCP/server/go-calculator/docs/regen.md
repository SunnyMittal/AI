# MCP Server Regeneration Prompt

This document contains a comprehensive prompt for regenerating this Model Context Protocol (MCP) server implementation from scratch. Follow this prompt with an AI assistant or use it as a specification document for manual implementation.

---

## Master Prompt

Create a production-ready Model Context Protocol (MCP) server in Go that provides mathematical calculation tools through HTTP/SSE transport. The server must be enterprise-grade, following Go best practices and implementing the MCP specification version 2025-03-26.

### Project Requirements

**Core Functionality:**
- Implement a fully compliant MCP server supporting JSON-RPC 2.0
- Provide four mathematical operations as MCP tools: add, subtract, multiply, divide
- Support HTTP/SSE (Server-Sent Events) transport for real-time communication
- Implement FastMCP-compatible session management with session IDs
- Follow MCP protocol version 2025-03-26

**Technical Stack:**
- Go 1.21 or higher
- Dependencies:
  - `github.com/joho/godotenv` v1.5.1 (environment configuration)
  - `go.uber.org/zap` v1.26.0 (structured logging)
  - Standard library for HTTP, JSON, and testing

**Architecture Requirements:**
- Follow standard Go project layout
- Implement clean architecture with separation of concerns
- Use idiomatic Go code with proper error handling
- Include comprehensive unit and integration tests
- Support graceful shutdown with signal handling
- Implement middleware chain for security, logging, and rate limiting

---

## Project Structure

Create the following directory structure:

```
go-calculator/
├── cmd/
│   └── server/
│       └── main.go              # Application entry point with graceful shutdown
├── internal/
│   ├── config/
│   │   ├── config.go            # Environment-based configuration
│   │   └── config_test.go       # Configuration validation tests
│   ├── logger/
│   │   └── logger.go            # Structured logging with zap
│   ├── mcp/
│   │   ├── protocol.go          # MCP protocol types and constants
│   │   ├── server.go            # MCP server logic and tool handlers
│   │   ├── transport.go         # HTTP/SSE transport with session management
│   │   └── transport_test.go    # Integration tests for transport
│   └── middleware/
│       └── middleware.go        # HTTP middleware (logging, security, rate limiting)
├── pkg/
│   └── calculator/
│       ├── calculator.go        # Calculator business logic
│       └── calculator_test.go   # Unit tests with benchmarks
├── docs/
│   └── USAGE.md                # API documentation
├── .env.example                # Example environment configuration
├── .gitignore                  # Git ignore rules
├── go.mod                      # Go module definition
└── README.md                   # Project documentation
```

---

## Detailed Implementation Guide

### 1. Initialize Go Module

```bash
go mod init github.com/mcp/go-calculator
go get github.com/joho/godotenv@v1.5.1
go get go.uber.org/zap@v1.26.0
```

### 2. Implement Core Calculator Logic (`pkg/calculator/calculator.go`)

**Requirements:**
- Create a `Calculator` struct (can be empty for stateless operations)
- Implement methods: `Add(a, b float64) float64`, `Subtract(a, b float64) float64`, `Multiply(a, b float64) float64`, `Divide(a, b float64) (float64, error)`
- Division must return error for division by zero: "division by zero is not allowed"
- Validate inputs for NaN and Infinity, return errors for invalid numbers
- All methods should use `context.Context` for cancellation support
- Format results to remove unnecessary decimal places (e.g., "8" not "8.0")

**Test Requirements (`pkg/calculator/calculator_test.go`):**
- Test each operation with positive, negative, and decimal numbers
- Test division by zero error handling
- Test invalid input handling (NaN, Infinity)
- Include benchmark tests for all operations
- Expected benchmark performance: <3 ns/op for add/subtract/multiply, <10 ns/op for divide

### 3. Implement MCP Protocol Types (`internal/mcp/protocol.go`)

**Constants to define:**
- `JSONRPCVersion = "2.0"`
- `ProtocolVersion = "2025-03-26"` (FastMCP compatible)
- `HeaderMCPSessionID = "mcp-session-id"`
- MCP methods: `initialize`, `tools/list`, `tools/call`
- JSON-RPC error codes: ParseError(-32700), InvalidRequest(-32600), MethodNotFound(-32601), InvalidParams(-32602), InternalError(-32603)

**Types to implement:**
- `JSONRPCRequest` with fields: JSONRPC, ID (interface{}), Method, Params (json.RawMessage)
- `JSONRPCResponse` with fields: JSONRPC, ID (interface{}), Result (interface{}), Error (*JSONRPCError)
- `JSONRPCError` with fields: Code (int), Message (string), Data (interface{})
- `InitializeParams` with ProtocolVersion, Capabilities, ClientInfo
- `InitializeResult` with ProtocolVersion, Capabilities, ServerInfo
- `Tool` with Name, Description, InputSchema
- `ToolCallParams` with Name, Arguments
- `ToolCallResult` with Content ([]Content), IsError (bool)
- Helper functions: `NewJSONRPCRequest`, `NewJSONRPCResponse`, `NewJSONRPCError`

**JSON Schema for Tools:**
Each tool must have proper JSON Schema with:
- Type: "object"
- Properties with type "number" for mathematical parameters
- Description for each property
- Required fields array

### 4. Implement MCP Server (`internal/mcp/server.go`)

**Server struct fields:**
- `name string` (server name)
- `version string` (server version)
- `calculator *calculator.Calculator`
- `tools []Tool` (pre-initialized tool definitions)

**Methods to implement:**
- `NewServer(version string) *Server` - Initialize with 4 calculator tools
- `HandleRequest(ctx context.Context, req *JSONRPCRequest) *JSONRPCResponse` - Main request dispatcher
- `handleInitialize(params InitializeParams) (InitializeResult, error)` - Return server info and capabilities
- `handleToolsList() ToolsListResult` - Return list of 4 calculator tools
- `handleToolsCall(ctx context.Context, params ToolCallParams) (ToolCallResult, error)` - Execute tool and return result

**Tool Definitions:**
1. **add**: "Add two numbers together" - params: a, b (both required, type: number)
2. **subtract**: "Subtract second number from first" - params: a, b (both required, type: number)
3. **multiply**: "Multiply two numbers together" - params: a, b (both required, type: number)
4. **divide**: "Divide first number by second" - params: a, b (both required, type: number)

**Error Handling:**
- Log all operations with structured logging (tool name, parameters, result/error)
- Wrap errors with context using fmt.Errorf
- Return proper JSON-RPC error codes
- Handle context cancellation gracefully

### 5. Implement HTTP/SSE Transport (`internal/mcp/transport.go`)

**Critical Requirements - FastMCP Compatible:**

**Session Management:**
- Create `session` struct with: id, createdAt, server
- Transport must maintain session map: `map[string]*session`
- Implement `generateSessionID()` returning 32 hex characters (16 random bytes)
- Session lifecycle:
  - Initialize creates new session if no session ID provided
  - Return session ID in `mcp-session-id` header
  - Non-initialize requests require valid session ID
  - DELETE /mcp terminates session

**HTTP Endpoints:**
- `POST /mcp` - JSON-RPC message endpoint (SSE response)
- `GET /mcp` - SSE stream for server-initiated messages
- `DELETE /mcp` - Session termination
- `GET /health` - Health check (JSON response)
- `GET /metrics` - Server metrics (JSON response)

**Request Handling (`handleMCPPost`):**
1. Validate `Accept: text/event-stream` header (return 406 if missing)
2. Get session ID from `mcp-session-id` header
3. Read and validate JSON body (1MB limit)
4. Parse JSON-RPC request
5. Handle session management:
   - Initialize: create session if not exists, return session ID
   - Other methods: require valid session ID
6. For notifications (no ID or method starts with "notifications/"): return 202 Accepted
7. Handle request and send SSE response with session ID

**SSE Response Format:**
```
Content-Type: text/event-stream
Cache-Control: no-cache, no-transform
mcp-session-id: <session-id>

event: message
data: {"jsonrpc":"2.0","id":1,"result":{...}}

```

**SSE Connection (`handleMCPGet`):**
- Require valid session ID in header
- Set headers: `Content-Type: text/event-stream`, `Cache-Control: no-cache, no-transform`
- Send connection event on connect
- Heartbeat every 30 seconds
- Handle context cancellation

**CORS Headers:**
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type, Accept, mcp-session-id`
- `Access-Control-Expose-Headers: mcp-session-id`

### 6. Implement Configuration (`internal/config/config.go`)

**Config struct:**
```go
type Config struct {
    Server ServerConfig
    Log    LogConfig
}

type ServerConfig struct {
    Host         string
    Port         string
    ReadTimeout  time.Duration
    WriteTimeout time.Duration
    IdleTimeout  time.Duration
}

type LogConfig struct {
    Level    string
    Encoding string
}
```

**Environment Variables with Defaults:**
- `SERVER_HOST=localhost`
- `SERVER_PORT=8000`
- `SERVER_READ_TIMEOUT=15s`
- `SERVER_WRITE_TIMEOUT=15s`
- `SERVER_IDLE_TIMEOUT=60s`
- `LOG_LEVEL=info`
- `LOG_ENCODING=json`

**Features:**
- Load from .env file using godotenv
- Validate configuration values
- Provide `Address()` method returning "host:port"
- Include tests for validation and defaults

### 7. Implement Logging (`internal/logger/logger.go`)

**Requirements:**
- Use zap logger globally
- Support levels: debug, info, warn, error
- Support encodings: json, console
- Export functions: `Initialize`, `Sync`, `Debug`, `Info`, `Warn`, `Error`, `Fatal`
- Include caller information in logs
- Use ISO8601 time format

### 8. Implement Middleware (`internal/middleware/middleware.go`)

**Middleware functions (all return http.Handler):**
- `Chain(h http.Handler, middleware ...Middleware) http.Handler` - Apply middleware in order
- `Logging(next http.Handler) http.Handler` - Log all requests with duration
- `Recovery(next http.Handler) http.Handler` - Recover from panics, log and return 500
- `SecurityHeaders(next http.Handler) http.Handler` - Add security headers
- `RequestValidator(maxBodySize int64) Middleware` - Validate content-type and body size
- `RateLimiter(rps int) Middleware` - Token bucket rate limiting per client IP
- `Timeout(duration time.Duration) Middleware` - Request timeout context

**Security Headers to add:**
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

### 9. Implement Main Application (`cmd/server/main.go`)

**Requirements:**
- Version constant: "1.0.0"
- Load configuration using config.Load()
- Initialize logger
- Create MCP server and transport
- Build middleware chain: Logging → Recovery → SecurityHeaders → RequestValidator(1MB) → RateLimiter(100) → Timeout(30s)
- Create http.Server with timeouts from config
- Start server in goroutine
- Handle signals: SIGINT, SIGTERM for graceful shutdown
- Graceful shutdown timeout: 30 seconds
- Exit with proper status codes (0 for success, 1 for error)
- Log all lifecycle events (startup, shutdown, errors)

### 10. Write Comprehensive Tests

**Unit Tests:**
- `pkg/calculator/calculator_test.go`: Test all operations, edge cases, benchmarks
- `internal/config/config_test.go`: Test loading, validation, defaults

**Integration Tests (`internal/mcp/transport_test.go`):**
- Test initialize request with session creation
- Test tools/list with valid session
- Test tools/call for all operations with valid session
- Test invalid JSON handling
- Test method not found error
- Test context cancellation
- Test missing Accept header (should return 406)
- Include benchmark test for tool calls
- Helper function `parseSSEResponse` to parse SSE formatted responses
- Compare JSON-RPC IDs as strings (to handle int vs float64 conversion)

**Test Requirements:**
- All tests must pass
- Use `httptest.NewRecorder` and `httptest.NewRequest` for HTTP tests
- Test both success and error paths
- Verify SSE response format
- Verify session management

### 11. Create Documentation Files

**.env.example:**
```
SERVER_PORT=8000
SERVER_HOST=localhost
SERVER_READ_TIMEOUT=15s
SERVER_WRITE_TIMEOUT=15s
SERVER_IDLE_TIMEOUT=60s
LOG_LEVEL=info
LOG_ENCODING=json
API_VERSION=v1
```

**.gitignore:**
```
# Binaries
bin/
*.exe
*.dll
*.so
*.dylib

# Test coverage
*.out
coverage.html

# Environment
.env

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
```

**README.md:**
- Include project overview with feature list
- Document all best practices implemented (see current README)
- Provide installation and setup instructions
- Document all API endpoints with request/response examples
- Include testing commands
- Document configuration options
- Add troubleshooting section

---

## MCP Protocol Specifics

### Initialize Flow
1. Client sends initialize request (no session ID required)
2. Server creates session and returns session ID in header
3. Server responds with protocol version and capabilities
4. Client sends notifications/initialized (optional)

### Tool Call Flow
1. Client sends tools/list request with session ID
2. Server returns list of 4 calculator tools
3. Client sends tools/call with tool name and arguments
4. Server validates arguments against schema
5. Server executes calculator operation with context
6. Server returns result or error in content array

### Session Management (FastMCP Compatible)
- Session ID format: 32 hex characters (e.g., "a1b2c3d4e5f6...")
- Passed via `mcp-session-id` HTTP header
- Initialize creates session if not provided
- All other requests require valid session
- DELETE /mcp terminates session
- Server maintains session → server mapping

### SSE Response Format
All JSON-RPC responses use SSE format:
```
event: message
data: <json-rpc-response>

```

---

## Critical Implementation Details

### 1. JSON Unmarshaling
When unmarshaling JSON, numeric IDs become float64. When comparing IDs in tests, use:
```go
fmt.Sprintf("%v", resp.ID) != fmt.Sprintf("%v", req.ID)
```

### 2. SSE Flushing
For SSE responses, must:
1. Write to buffered writer
2. Flush buffered writer
3. Flush http.ResponseWriter (if it implements http.Flusher)

### 3. Context Propagation
- Get context from `r.Context()` in HTTP handlers
- Pass context to calculator operations
- Check context cancellation in tool execution
- Return appropriate errors when context is cancelled

### 4. Error Messages
Calculator errors should be descriptive:
- Division by zero: "division by zero is not allowed"
- Invalid number: "invalid number: %v is %s" (e.g., NaN, Infinity)
- Context cancelled: "context canceled"

### 5. Number Formatting
Results should be formatted to remove unnecessary decimals:
- 8.0 → "8"
- 2.5 → "2.5"
- Use `strconv.FormatFloat(result, 'f', -1, 64)`

---

## Testing Checklist

Before considering implementation complete, verify:

- [ ] All unit tests pass: `go test ./...`
- [ ] Tests run without cache: `go test ./... -count=1`
- [ ] Benchmarks run successfully: `go test -bench=. ./...`
- [ ] Code builds: `go build ./...`
- [ ] Server starts and listens on configured port
- [ ] Health endpoint returns 200: `curl http://localhost:8000/health`
- [ ] Metrics endpoint returns active connections
- [ ] Initialize request creates session and returns session ID
- [ ] Tools/list requires valid session
- [ ] Tools/call executes calculations correctly
- [ ] Missing Accept header returns 406
- [ ] Invalid session ID returns 404
- [ ] Graceful shutdown works (Ctrl+C)
- [ ] Logs are structured JSON (when LOG_ENCODING=json)
- [ ] All 4 calculator operations work correctly
- [ ] Division by zero returns error in isError format
- [ ] SSE responses are properly formatted

---

## Validation Commands

After implementation, run these commands to validate:

```bash
# Install dependencies
go mod download

# Format code
gofmt -w .

# Vet code
go vet ./...

# Run tests
go test ./... -v

# Run tests with coverage
go test -cover ./...

# Run benchmarks
go test -bench=. -benchmem ./pkg/calculator/

# Build
go build -o bin/server cmd/server/main.go

# Run server
./bin/server

# Test health endpoint
curl http://localhost:8000/health

# Test metrics
curl http://localhost:8000/metrics

# Test initialize (should create session)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  -i

# Extract session ID from response header and use for subsequent requests
```

---

## Success Criteria

The implementation is complete and correct when:

1. **Functionality**: All 4 calculator operations work correctly via MCP protocol
2. **Protocol Compliance**: Fully implements MCP specification 2025-03-26 with FastMCP session management
3. **Testing**: All tests pass with >80% code coverage
4. **Performance**: Benchmarks meet performance targets (<10ns/op for operations)
5. **Production Ready**: Implements all best practices (logging, error handling, security, graceful shutdown)
6. **Documentation**: Complete README with API examples and usage instructions
7. **Code Quality**: Passes `go vet`, follows Go idioms, properly formatted
8. **Session Management**: Correctly handles session creation, validation, and termination
9. **SSE Transport**: Properly formats responses in Server-Sent Events format
10. **Error Handling**: Returns proper JSON-RPC error codes and descriptive messages

---

## Common Pitfalls to Avoid

1. **Don't** use plain JSON responses - all responses must be in SSE format for POST /mcp
2. **Don't** forget to validate Accept header - must include "text/event-stream"
3. **Don't** use context package directly if not needed - it's imported but not referenced
4. **Don't** compare interface{} IDs directly - use string formatting for comparison
5. **Don't** forget to flush SSE responses properly (bufio.Writer then http.Flusher)
6. **Don't** allow requests without session ID except for initialize
7. **Don't** forget to set mcp-session-id header in all responses
8. **Don't** return 200 for errors - use appropriate HTTP status codes
9. **Don't** ignore context cancellation - check and return appropriate errors
10. **Don't** forget CORS headers - required for browser-based clients

---

## Extension Points

Once base implementation is complete, consider adding:

- More mathematical tools (power, sqrt, modulo)
- Persistent sessions with storage backend
- WebSocket transport in addition to SSE
- Prometheus metrics integration
- Distributed tracing with OpenTelemetry
- Docker and Kubernetes deployment configs
- CI/CD pipeline configuration
- API authentication and authorization
- Request/response caching
- Multiple calculator instances with load balancing

---

## Version History

- **1.0.0**: Initial implementation with 4 calculator tools, FastMCP-compatible session management, SSE transport

---

*End of Regeneration Prompt*
