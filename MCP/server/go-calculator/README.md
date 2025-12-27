# Go Calculator MCP Server

A high-performance Model Context Protocol (MCP) server written in Go that provides mathematical calculation tools through streamable HTTP transport.

## Features

- **Mathematical Operations**: Addition, subtraction, multiplication, and division
- **MCP Protocol**: Fully compliant with Model Context Protocol specification (2024-11-05)
- **HTTP/SSE Transport**: Real-time communication using Server-Sent Events
- **Production-Ready**: Implements Go best practices for enterprise applications

### Best Practices Implemented

- ✅ **Structured Logging**: Using uber/zap with configurable levels and formats
- ✅ **Idiomatic Error Handling**: Proper error wrapping and meaningful error messages
- ✅ **Modular Architecture**: Clear separation of concerns across packages
- ✅ **Configuration Management**: Environment-based configuration with validation
- ✅ **Comprehensive Testing**: Unit and integration tests with benchmarks
- ✅ **Standard Project Layout**: Following Go project structure conventions
- ✅ **Concurrency Support**: Efficient handling of concurrent requests
- ✅ **Input Validation**: Protection against injection attacks and invalid data
- ✅ **Graceful Shutdown**: Signal handling for clean application termination
- ✅ **Performance Monitoring**: Built-in metrics and health endpoints
- ✅ **Dependency Management**: Go modules for reliable dependency tracking
- ✅ **API Versioning**: Versioned HTTP endpoints
- ✅ **Context Usage**: Request cancellation, timeouts, and scoped values

## Project Structure

```
go-calculator/
├── cmd/
│   └── server/
│       └── main.go              # Application entry point
├── internal/
│   ├── config/
│   │   ├── config.go            # Configuration management
│   │   └── config_test.go       # Configuration tests
│   ├── logger/
│   │   └── logger.go            # Structured logging
│   ├── mcp/
│   │   ├── protocol.go          # MCP protocol types
│   │   ├── server.go            # MCP server logic
│   │   ├── transport.go         # HTTP/SSE transport
│   │   └── transport_test.go    # Transport integration tests
│   └── middleware/
│       └── middleware.go        # HTTP middleware (logging, security, etc.)
├── pkg/
│   └── calculator/
│       ├── calculator.go        # Calculator business logic
│       └── calculator_test.go   # Calculator unit tests
├── docs/
│   └── prompt.md               # Project requirements
├── .env.example                # Example environment configuration
├── .gitignore                  # Git ignore rules
├── go.mod                      # Go module definition
└── README.md                   # This file
```

## Installation

### Prerequisites

- Go 1.21 or higher
- Git (for cloning the repository)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd go-calculator
```

2. Install dependencies:
```bash
go mod download
```

3. Create environment configuration:
```bash
cp .env.example .env
```

4. Configure environment variables (optional):
```bash
# Edit .env file with your preferred settings
nano .env
```

## Configuration

The server can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_PORT` | `8200` | Port to listen on |
| `SERVER_HOST` | `localhost` | Host to bind to |
| `SERVER_READ_TIMEOUT` | `15s` | HTTP read timeout |
| `SERVER_WRITE_TIMEOUT` | `15s` | HTTP write timeout |
| `SERVER_IDLE_TIMEOUT` | `60s` | HTTP idle timeout |
| `LOG_LEVEL` | `info` | Logging level (debug, info, warn, error) |
| `LOG_ENCODING` | `json` | Log format (json, console) |
| `API_VERSION` | `v1` | API version |

## Running the Server

### Development Mode

```bash
go run cmd/server/main.go
```

### Production Build

```bash
# Build the binary
go build -o bin/calculator-server cmd/server/main.go

# Run the server
./bin/calculator-server
```

### Using Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o server cmd/server/main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/server .
EXPOSE 8200
CMD ["./server"]
```

Build and run:
```bash
docker build -t go-calculator .
docker run -p 8200:8200 go-calculator
```

## API Documentation

### Endpoints

#### POST /mcp/v1/messages
JSON-RPC 2.0 endpoint for MCP protocol messages.

#### GET /mcp/v1/sse
Server-Sent Events endpoint for real-time streaming.

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-14T12:00:00Z",
  "service": "go-calculator"
}
```

#### GET /metrics
Performance metrics endpoint.

**Response:**
```json
{
  "active_connections": 5,
  "timestamp": "2025-12-14T12:00:00Z"
}
```

### MCP Protocol

#### Initialize

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "client-name",
      "version": "1.0.0"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {
        "listChanged": false
      }
    },
    "serverInfo": {
      "name": "go-calculator",
      "version": "1.0.0"
    }
  }
}
```

#### List Tools

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "add",
        "description": "Add two numbers together",
        "inputSchema": {
          "type": "object",
          "properties": {
            "a": {"type": "number", "description": "The first number"},
            "b": {"type": "number", "description": "The second number"}
          },
          "required": ["a", "b"]
        }
      }
      // ... other tools
    ]
  }
}
```

#### Call Tool

**Request:**
```json
{
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
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "8"
      }
    ],
    "isError": false
  }
}
```

### Available Tools

#### add
Adds two numbers together.
- **Parameters**: `a` (number), `b` (number)
- **Returns**: Sum of a and b

#### subtract
Subtracts the second number from the first.
- **Parameters**: `a` (number), `b` (number)
- **Returns**: Difference (a - b)

#### multiply
Multiplies two numbers together.
- **Parameters**: `a` (number), `b` (number)
- **Returns**: Product of a and b

#### divide
Divides the first number by the second.
- **Parameters**: `a` (number), `b` (number)
- **Returns**: Quotient (a / b)
- **Error**: Returns error if b is zero

## Testing

### Clear test results

```powershell
go clean -testcache
```

### Run All Tests

```bash
go test ./...
```

### Run Tests with Coverage

```bash
go test -cover ./...
```

### Run Specific Package Tests

```bash
# Test calculator package
go test ./pkg/calculator/

# Test MCP package
go test ./internal/mcp/

# Test config package
go test ./internal/config/
```

### Run Benchmarks

```bash
go test -bench=. ./...
```

### Generate Coverage Report

```bash
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

## Performance

The server is optimized for high performance:

- **Efficient Algorithms**: O(1) mathematical operations
- **Concurrent Request Handling**: Goroutines for parallel processing
- **Connection Pooling**: Efficient resource management
- **Rate Limiting**: 100 requests per second per client
- **Request Timeout**: 30-second default timeout
- **Body Size Limit**: 1MB maximum request size

### Benchmarks

Run benchmarks to verify performance:

```bash
go test -bench=. -benchmem ./pkg/calculator/
```

Expected results on modern hardware:
- Add: ~0.3 ns/op
- Subtract: ~0.3 ns/op
- Multiply: ~0.3 ns/op
- Divide: ~2.0 ns/op

## Security

### Implemented Security Measures

1. **Input Validation**: All inputs validated before processing
2. **Rate Limiting**: Prevents DoS attacks
3. **Request Size Limits**: Prevents memory exhaustion
4. **Security Headers**: X-Frame-Options, X-Content-Type-Options, etc.
5. **Error Sanitization**: No sensitive data in error responses
6. **Context Timeouts**: Prevents long-running requests
7. **Number Validation**: Checks for NaN and Infinity

### Best Practices

- Always run behind a reverse proxy (nginx, Caddy) in production
- Use TLS/HTTPS for encrypted communication
- Set appropriate CORS policies
- Monitor logs for suspicious activity
- Keep dependencies updated

## Monitoring

### Logs

Logs are output in JSON format (configurable to console):

```json
{
  "level": "info",
  "timestamp": "2025-12-14T12:00:00.000Z",
  "caller": "mcp/server.go:123",
  "msg": "tool execution succeeded",
  "tool": "add",
  "result": 8
}
```

### Metrics

Access metrics at `GET /metrics`:

```bash
curl http://localhost:8200/metrics
```

### Health Checks

Monitor server health:

```bash
curl http://localhost:8200/health
```

## Graceful Shutdown

The server handles shutdown signals (SIGINT, SIGTERM) gracefully:

1. Stops accepting new connections
2. Waits for existing requests to complete (30s timeout)
3. Closes all connections
4. Exits cleanly

To trigger shutdown:
```bash
# Send SIGINT (Ctrl+C)
# Or send SIGTERM
kill -TERM <pid>
```

## Development

### Code Style

Follow standard Go conventions:
- Use `gofmt` for formatting
- Run `go vet` for static analysis
- Use `golangci-lint` for linting

```bash
# Format code
gofmt -w .

# Vet code
go vet ./...

# Lint (if golangci-lint is installed)
golangci-lint run
```

### Adding New Tools

1. Add tool definition in `internal/mcp/server.go`:
```go
{
    Name:        "newtool",
    Description: "Description of new tool",
    InputSchema: InputSchema{
        // Define schema
    },
}
```

2. Implement tool logic in `executeTool` method
3. Add tests in `internal/mcp/transport_test.go`

## Troubleshooting

### Server won't start

- Check if port is already in use: `lsof -i :8200` (Unix) or `netstat -ano | findstr :8200` (Windows)
- Verify configuration in `.env` file
- Check logs for detailed error messages

### Tests failing

- Ensure Go version is 1.21+
- Run `go mod download` to update dependencies
- Check for port conflicts during integration tests

### High memory usage

- Check `SERVER_IDLE_TIMEOUT` configuration
- Monitor active connections at `/metrics`
- Verify no connection leaks in SSE endpoint

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Guidelines

- Use conventional commits format
- Include tests for new features
- Update documentation as needed
- Ensure all tests pass

## License

This project is provided as-is for educational and commercial use.

## Support

For issues, questions, or contributions, please open an issue on the repository.

## Acknowledgments

- Built following MCP specification
- Uses uber/zap for high-performance logging
- Inspired by Go best practices and community standards
