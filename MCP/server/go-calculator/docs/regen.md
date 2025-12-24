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
│   ├── middleware/
│   │   └── middleware.go        # HTTP middleware (logging, security, rate limiting)
│   └── telemetry/
│       └── telemetry.go         # OpenTelemetry instrumentation with Phoenix
├── pkg/
│   └── calculator/
│       ├── calculator.go        # Calculator business logic
│       └── calculator_test.go   # Unit tests with benchmarks
├── tests/
│   └── performance/
│       ├── k6/
│       │   ├── scenarios/
│       │   │   ├── load-test.js         # Baseline load testing
│       │   │   ├── stress-test.js       # Find breaking points
│       │   │   ├── endurance-test.js    # Long-running stability
│       │   │   ├── spike-test.js        # Sudden traffic spikes
│       │   │   └── benchmark-tools.js   # Individual tool benchmarks
│       │   └── lib/
│       │       ├── mcp-client.js        # MCP protocol client for k6
│       │       ├── test-data.js         # Test data generators
│       │       └── thresholds.js        # Performance SLIs/SLOs
│       ├── scripts/
│       │   ├── run-load-test.ps1        # Load test runner (Windows)
│       │   ├── run-load-test.sh         # Load test runner (Linux/macOS)
│       │   ├── run-stress-test.ps1      # Stress test runner (Windows)
│       │   ├── run-stress-test.sh       # Stress test runner (Linux/macOS)
│       │   ├── run-endurance-test.ps1   # Endurance test runner (Windows)
│       │   ├── run-endurance-test.sh    # Endurance test runner (Linux/macOS)
│       │   ├── setup-k6.sh              # k6 setup script
│       │   └── compare-results.sh       # Results comparison
│       ├── results/             # Test results directory (gitignored)
│       └── README.md            # Performance testing documentation
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

### 11. Implement Performance Tests with k6 (`tests/performance/`)

**Prerequisites:**
- Install k6 load testing tool
- Windows: `choco install k6` or `winget install k6`
- macOS: `brew install k6`
- Linux: See [k6 installation docs](https://k6.io/docs/get-started/installation/)

**MCP Client Library (`k6/lib/mcp-client.js`):**
Create a k6-compatible MCP client with functions:
- `initializeSession()` - Initialize MCP session and return session ID
- `callTool(sessionId, toolName, args)` - Call a calculator tool
- `deleteSession(sessionId)` - Clean up session
- Parse SSE responses to extract JSON-RPC data

**Test Data Library (`k6/lib/test-data.js`):**
- Random number generators for test inputs
- Operation selector for distributing load across all 4 operations

**Thresholds Library (`k6/lib/thresholds.js`):**
Define performance SLIs/SLOs:
- p95 latency < 100ms (stretch: < 75ms)
- p99 latency < 200ms (stretch: < 150ms)
- Throughput > 1000 req/s (stretch: > 2000 req/s)
- Error rate < 0.1% (stretch: < 0.05%)

**Test Scenarios:**

1. **Load Test (`scenarios/load-test.js`):**
   - Duration: ~14 minutes
   - Purpose: Baseline performance under normal/peak load
   - Profile: Ramp 0→50→100 VUs with sustain periods
   - Success criteria: p95 < 100ms, throughput > 1000 req/s

2. **Stress Test (`scenarios/stress-test.js`):**
   - Duration: ~25 minutes
   - Purpose: Find system breaking points
   - Profile: Progressive ramp to 800 VUs
   - Success criteria: Identify maximum capacity

3. **Endurance Test (`scenarios/endurance-test.js`):**
   - Duration: 2+ hours
   - Purpose: Long-running stability, memory leak detection
   - Profile: Sustain 50 VUs for 2 hours
   - Success criteria: No memory leaks, stable performance

4. **Spike Test (`scenarios/spike-test.js`):**
   - Duration: ~12 minutes
   - Purpose: Test recovery from sudden traffic bursts
   - Profile: 5 cycles of 10→200→10 VUs
   - Success criteria: Quick recovery, low error rate

5. **Benchmark Test (`scenarios/benchmark-tools.js`):**
   - Duration: ~5 minutes
   - Purpose: Benchmark individual operations
   - Profile: Isolated testing per operation (add, subtract, multiply, divide)
   - Success criteria: Compare with Go micro-benchmarks

**Runner Scripts:**
Create both PowerShell (.ps1) and Bash (.sh) scripts for:
- `run-load-test` - Start server, run load test, save results
- `run-stress-test` - Start server, run stress test, save results
- `run-endurance-test` - Start server, run 2+ hour test, save results
- Scripts should handle server startup/shutdown and output results to timestamped files

**Results Directory:**
- Create `tests/performance/results/` with `.gitkeep`
- Results saved with timestamps: `load-YYYYMMDD-HHMMSS.json`

### 12. Implement Observability with OpenTelemetry and Phoenix (`internal/telemetry/`)

**Dependencies:**
Add to `go.mod`:
```bash
go get go.opentelemetry.io/otel
go get go.opentelemetry.io/otel/sdk
go get go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp
go get go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp
go get go.opentelemetry.io/otel/trace
```

**Configuration Integration (`internal/config/config.go`):**

Add telemetry configuration to the Config struct:
```go
// TelemetryConfig holds observability configuration
type TelemetryConfig struct {
    PhoenixEndpoint string
    ProjectName     string
}

// Add to main Config struct
type Config struct {
    Server    ServerConfig
    Log       LogConfig
    API       APIConfig
    Telemetry TelemetryConfig  // Add this
}
```

Load from environment in `Load()` function:
```go
Telemetry: TelemetryConfig{
    PhoenixEndpoint: getEnvOrDefault("PHOENIX_ENDPOINT", "http://localhost:6006"),
    ProjectName:     getEnvOrDefault("PHOENIX_PROJECT_NAME", "go-calculator"),
},
```

**Telemetry Package (`internal/telemetry/telemetry.go`):**

Create comprehensive telemetry package with:

1. **Config Structure:**
```go
type Config struct {
    ServiceName     string
    ServiceVersion  string
    PhoenixEndpoint string
    ProjectName     string
}
```

2. **LoadConfig Function:**
```go
func LoadConfig(serviceName, version, endpoint, projectName string) Config {
    endpoint = strings.TrimSuffix(endpoint, "/")
    return Config{
        ServiceName:     serviceName,
        ServiceVersion:  version,
        PhoenixEndpoint: endpoint,
        ProjectName:     projectName,
    }
}
```

3. **Phoenix Health Check & Project Management:**
```go
func ensureProjectExists(ctx context.Context, phoenixURL, projectName string) error {
    // Verify Phoenix is reachable
    // Phoenix auto-creates projects via x-project-name header
    // Health check implementation:
    // - GET request to Phoenix base URL
    // - 5 second timeout
    // - Return error if not reachable (warn, don't fail server)
}
```

4. **OpenTelemetry Initialization:**
```go
func Initialize(ctx context.Context, cfg Config) (func(context.Context) error, error) {
    // 1. Check Phoenix availability
    if err := ensureProjectExists(ctx, cfg.PhoenixEndpoint, cfg.ProjectName); err != nil {
        return nil, fmt.Errorf("Phoenix project check failed: %w", err)
    }

    // 2. Create OTLP HTTP exporter with Phoenix headers
    endpoint := strings.TrimPrefix(cfg.PhoenixEndpoint, "http://")
    endpoint = strings.TrimPrefix(endpoint, "https://")

    headers := map[string]string{}
    if cfg.ProjectName != "" {
        headers["x-project-name"] = cfg.ProjectName  // Critical for project routing
    }

    exporter, err := otlptracehttp.New(ctx,
        otlptracehttp.WithEndpoint(endpoint),
        otlptracehttp.WithURLPath("/v1/traces"),
        otlptracehttp.WithInsecure(),
        otlptracehttp.WithHeaders(headers),  // Project name header
    )

    // 3. Create resource with service metadata
    res, err := resource.New(ctx,
        resource.WithAttributes(
            semconv.ServiceName(cfg.ServiceName),
            semconv.ServiceVersion(cfg.ServiceVersion),
            attribute.String("mcp.protocol_version", "2025-03-26"),
            attribute.String("phoenix.project", cfg.ProjectName),
        ),
    )

    // 4. Create TracerProvider with batching
    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exporter),
        sdktrace.WithResource(res),
        sdktrace.WithSampler(sdktrace.AlwaysSample()),
    )

    // 5. Set global providers
    otel.SetTracerProvider(tp)
    otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
        propagation.TraceContext{},
        propagation.Baggage{},
    ))

    // Return shutdown function
    return tp.Shutdown, nil
}
```

5. **Tracer Helper:**
```go
func Tracer(name string) trace.Tracer {
    return otel.Tracer(name)
}
```

**HTTP Instrumentation (`internal/mcp/transport.go`):**

Add otelhttp wrapper:
```go
import "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"

// Handler returns an instrumented HTTP handler
func (t *Transport) Handler() http.Handler {
    return otelhttp.NewHandler(t, "mcp-server",
        otelhttp.WithSpanNameFormatter(func(_ string, r *http.Request) string {
            return fmt.Sprintf("%s %s", r.Method, r.URL.Path)
        }),
    )
}
```

**MCP Server Instrumentation (`internal/mcp/server.go`):**

Add tracing to request handlers:
```go
import (
    "github.com/mcp/go-calculator/internal/telemetry"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/codes"
    "go.opentelemetry.io/otel/trace"
)

func (s *Server) HandleRequest(ctx context.Context, req *JSONRPCRequest) *JSONRPCResponse {
    tracer := telemetry.Tracer("go-calculator")
    ctx, span := tracer.Start(ctx, "mcp.request",
        trace.WithAttributes(
            attribute.String("mcp.method", req.Method),
            attribute.String("rpc.system", "jsonrpc"),
            attribute.String("rpc.jsonrpc.version", JSONRPCVersion),
        ),
    )
    defer span.End()

    // Handler logic with error recording
    // span.RecordError(err)
    // span.SetStatus(codes.Error, "error message")
}

func (s *Server) handleToolsCall(ctx context.Context, req *JSONRPCRequest) *JSONRPCResponse {
    span := trace.SpanFromContext(ctx)

    // Add tool-specific attributes
    span.SetAttributes(
        attribute.String("mcp.tool.name", params.Name),
        attribute.Float64("mcp.tool.arg.a", a),
        attribute.Float64("mcp.tool.arg.b", b),
    )

    // On success
    span.SetAttributes(
        attribute.Float64("mcp.tool.result", result),
        attribute.Bool("mcp.tool.error", false),
    )

    // On error
    span.RecordError(err)
    span.SetStatus(codes.Error, "Tool execution failed")
    span.SetAttributes(attribute.Bool("mcp.tool.error", true))
}
```

**Main Application Integration (`cmd/server/main.go`):**

```go
import "github.com/mcp/go-calculator/internal/telemetry"

func run() int {
    // After config and logger initialization
    ctx := context.Background()
    telemetryCfg := telemetry.LoadConfig(
        "go-calculator",
        version,
        cfg.Telemetry.PhoenixEndpoint,
        cfg.Telemetry.ProjectName,
    )

    shutdownTelemetry, err := telemetry.Initialize(ctx, telemetryCfg)
    if err != nil {
        logger.Warn("failed to initialize telemetry, continuing without tracing",
            zap.Error(err),
        )
    } else {
        logger.Info("telemetry initialized",
            zap.String("endpoint", telemetryCfg.PhoenixEndpoint),
            zap.String("project", telemetryCfg.ProjectName),
        )
        defer func() {
            shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
            defer cancel()
            if err := shutdownTelemetry(shutdownCtx); err != nil {
                logger.Error("failed to shutdown telemetry", zap.Error(err))
            }
        }()
    }

    // Use instrumented handler
    handler := middleware.Chain(
        transport.Handler(), // Wrapped with otelhttp
        // ... other middleware
    )
}
```

**Trace Attributes Standard:**

| Attribute | Description | Example |
|-----------|-------------|---------|
| `service.name` | Service identifier | `go-calculator` |
| `service.version` | Semantic version | `1.0.0` |
| `mcp.protocol_version` | MCP spec version | `2025-03-26` |
| `mcp.method` | JSON-RPC method | `tools/call` |
| `mcp.tool.name` | Tool being called | `add`, `divide` |
| `mcp.tool.arg.a` | First operand | `5.0` |
| `mcp.tool.arg.b` | Second operand | `3.0` |
| `mcp.tool.result` | Calculation result | `8.0` |
| `mcp.tool.error` | Error flag | `false` |
| `mcp.client.name` | Client name | `test-client` |
| `mcp.client.version` | Client version | `1.0.0` |

**Testing Telemetry:**

1. Start Phoenix: `phoenix serve` (or `docker run -p 6006:6006 arizephoenix/phoenix:latest`)
2. Server logs should show: `telemetry initialized`
3. Make MCP requests
4. View traces at `http://localhost:6006`
5. Verify traces appear under project "go-calculator"

### 13. Create Documentation Files

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
PHOENIX_ENDPOINT=http://localhost:6006
PHOENIX_PROJECT_NAME=go-calculator
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
- [ ] k6 is installed and available
- [ ] Quick load test passes: `k6 run --duration 30s --vus 10 tests/performance/k6/scenarios/load-test.js`
- [ ] Performance targets met: p95 < 100ms, error rate < 0.1%
- [ ] Phoenix is installed and running: `phoenix serve` or Docker
- [ ] Telemetry initializes successfully (check server logs)
- [ ] Traces appear in Phoenix UI at `http://localhost:6006`
- [ ] Traces are routed to correct project (go-calculator)

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

# Performance Testing with k6

# Install k6 (Windows)
choco install k6
# or: winget install k6

# Install k6 (macOS)
brew install k6

# Quick 30-second load test
k6 run --duration 30s --vus 10 tests/performance/k6/scenarios/load-test.js

# Full load test (~14 minutes) - Windows
.\tests\performance\scripts\run-load-test.ps1

# Full load test (~14 minutes) - Linux/macOS
bash tests/performance/scripts/run-load-test.sh

# Stress test (~25 minutes) - Windows
.\tests\performance\scripts\run-stress-test.ps1

# Stress test (~25 minutes) - Linux/macOS
bash tests/performance/scripts/run-stress-test.sh

# Benchmark individual operations
k6 run tests/performance/k6/scenarios/benchmark-tools.js

# Spike test
k6 run tests/performance/k6/scenarios/spike-test.js
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
11. **Performance Testing**: k6 performance tests pass with:
    - p95 latency < 100ms under load
    - Error rate < 0.1%
    - Server handles 100+ concurrent users
    - All 5 test scenarios (load, stress, endurance, spike, benchmark) available
12. **Observability**: OpenTelemetry tracing with Phoenix integration:
    - Telemetry package properly configured and initialized
    - Phoenix health check passes on startup
    - Traces sent to correct project via `x-project-name` header
    - HTTP requests instrumented with otelhttp
    - MCP handlers traced with custom attributes
    - Trace context propagated through request lifecycle
    - Graceful telemetry shutdown on server termination

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
11. **Don't** forget to add `x-project-name` header to OTLP exporter - Phoenix needs this for project routing
12. **Don't** hard-code Phoenix endpoint - always load from configuration
13. **Don't** fail server startup if Phoenix is unavailable - log warning and continue
14. **Don't** forget to pass context through instrumented handlers - needed for span propagation

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
- HTML performance reports generation from k6 results
- Automated performance regression detection in CI

---

## Version History

- **1.1.0**: Added comprehensive k6 performance testing suite with load, stress, endurance, spike, and benchmark tests. Cross-platform support (Windows PowerShell and Linux/macOS Bash scripts).
- **1.0.0**: Initial implementation with 4 calculator tools, FastMCP-compatible session management, SSE transport

---

*End of Regeneration Prompt*
