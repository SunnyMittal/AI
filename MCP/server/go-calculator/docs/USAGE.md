# Usage Guide

This guide provides detailed instructions on how to use the Go Calculator MCP Server.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Configuration](#configuration)
3. [Running the Server](#running-the-server)
4. [Making Requests](#making-requests)
5. [Error Handling](#error-handling)
6. [Performance Tuning](#performance-tuning)
7. [Monitoring](#monitoring)
8. [Production Deployment](#production-deployment)

## Getting Started

### Prerequisites

Ensure you have:
- Go 1.21 or higher installed
- A terminal or command prompt
- `curl` or a HTTP client for testing
- (Optional) `jq` for JSON formatting

### Quick Start

1. **Clone and setup:**
   ```bash
   cd go-calculator
   go mod download
   ```

2. **Run the server:**
   ```bash
   go run cmd/server/main.go
   ```

3. **Test the server:**
   ```bash
   curl http://localhost:8200/health
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Server settings
SERVER_PORT=8200
SERVER_HOST=localhost
SERVER_READ_TIMEOUT=15s
SERVER_WRITE_TIMEOUT=15s
SERVER_IDLE_TIMEOUT=60s

# Logging settings
LOG_LEVEL=info        # debug, info, warn, error
LOG_ENCODING=json     # json, console

# API settings
API_VERSION=v1
```

### Configuration Best Practices

**Development:**
```bash
LOG_LEVEL=debug
LOG_ENCODING=console
```

**Production:**
```bash
LOG_LEVEL=info
LOG_ENCODING=json
SERVER_READ_TIMEOUT=10s
SERVER_WRITE_TIMEOUT=10s
```

## Running the Server

### Development Mode

```bash
# Using go run
go run cmd/server/main.go

# With custom port
SERVER_PORT=9090 go run cmd/server/main.go
```

### Production Mode

```bash
# Build binary
go build -o bin/calculator-server cmd/server/main.go

# Run binary
./bin/calculator-server

# Run with nohup (Unix)
nohup ./bin/calculator-server > server.log 2>&1 &

# Run as systemd service (recommended for production)
# See docs/systemd-service.md
```

### Common Commands

```bash
# Build the server
go build -o bin/calculator-server cmd/server/main.go

# Run the server
go run cmd/server/main.go

# Run tests
go test ./...

# Generate coverage report
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out

# Run benchmarks
go test -bench=. -benchmem ./...

# Format code
gofmt -w .

# Clean build artifacts (Windows PowerShell)
Remove-Item -Recurse -Force bin, coverage.out, coverage.html -ErrorAction SilentlyContinue

# Clean build artifacts (Linux/macOS)
rm -rf bin coverage.out coverage.html
```

## Making Requests

### Using cURL

#### Health Check
```bash
curl http://localhost:8200/health
```

#### Initialize MCP Session
```bash
curl -X POST http://localhost:8200/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "my-client",
        "version": "1.0.0"
      }
    }
  }'
```

#### List Tools
```bash
curl -X POST http://localhost:8200/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
  }'
```

#### Call Tool (Add)
```bash
curl -X POST http://localhost:8200/mcp/v1/messages \
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
  }'
```

### Using Example Scripts

#### Bash Script
```bash
chmod +x examples/example_requests.sh
./examples/example_requests.sh
```

#### Python Client
```bash
pip install requests
python examples/example_client.py
```

### Using Programming Languages

#### JavaScript (Node.js)
```javascript
const fetch = require('node-fetch');

async function callTool(name, args) {
  const response = await fetch('http://localhost:8200/mcp/v1/messages', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: 1,
      method: 'tools/call',
      params: { name, arguments: args }
    })
  });
  return response.json();
}

// Example: Add two numbers
callTool('add', { a: 5, b: 3 })
  .then(result => console.log(result));
```

#### Python
```python
import requests

def call_tool(name, args):
    response = requests.post(
        'http://localhost:8200/mcp/v1/messages',
        json={
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/call',
            'params': {'name': name, 'arguments': args}
        }
    )
    return response.json()

# Example: Add two numbers
result = call_tool('add', {'a': 5, 'b': 3})
print(result)
```

#### Go
```go
package main

import (
    "bytes"
    "encoding/json"
    "net/http"
)

type Request struct {
    JSONRPC string      `json:"jsonrpc"`
    ID      int         `json:"id"`
    Method  string      `json:"method"`
    Params  interface{} `json:"params,omitempty"`
}

func callTool(name string, args map[string]float64) (map[string]interface{}, error) {
    req := Request{
        JSONRPC: "2.0",
        ID:      1,
        Method:  "tools/call",
        Params: map[string]interface{}{
            "name":      name,
            "arguments": args,
        },
    }

    body, _ := json.Marshal(req)
    resp, err := http.Post(
        "http://localhost:8200/mcp/v1/messages",
        "application/json",
        bytes.NewReader(body),
    )
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var result map[string]interface{}
    json.NewDecoder(resp.Body).Decode(&result)
    return result, nil
}
```

## Error Handling

### Common Errors

#### Parse Error (-32700)
```json
{
  "jsonrpc": "2.0",
  "id": null,
  "error": {
    "code": -32700,
    "message": "Parse error",
    "data": "Invalid JSON"
  }
}
```

**Solution:** Ensure request body is valid JSON.

#### Method Not Found (-32601)
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found"
  }
}
```

**Solution:** Check method name (initialize, tools/list, tools/call).

#### Invalid Params (-32602)
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid parameters",
    "data": "missing required arguments: 'a' and 'b' are required"
  }
}
```

**Solution:** Verify all required parameters are provided.

#### Division by Zero
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "division by zero is not allowed"
    }],
    "isError": true
  }
}
```

**Solution:** Don't divide by zero.

### Error Response Format

Tool errors are returned in the result:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{"type": "text", "text": "error message"}],
    "isError": true
  }
}
```

Protocol errors are returned as JSON-RPC errors:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid parameters"
  }
}
```

## Performance Tuning

### Optimize Configuration

For high-throughput scenarios:

```bash
# Increase timeouts
SERVER_READ_TIMEOUT=30s
SERVER_WRITE_TIMEOUT=30s
SERVER_IDLE_TIMEOUT=120s

# Reduce log verbosity
LOG_LEVEL=warn
```

### Rate Limiting

The server includes built-in rate limiting (100 req/s per IP). To adjust:

Edit `cmd/server/main.go`:
```go
middleware.RateLimiter(1000),  // 1000 requests per second
```

### Connection Pooling

For clients making many requests:

**Python:**
```python
session = requests.Session()
# Reuse session for all requests
```

**Go:**
```go
client := &http.Client{
    Transport: &http.Transport{
        MaxIdleConns:       100,
        IdleConnTimeout:    90 * time.Second,
    },
}
```

### Benchmark Results

Run benchmarks:
```bash
go test -bench=. -benchmem ./...
```

Expected performance:
- **Add/Subtract/Multiply:** ~0.3 ns/op
- **Divide:** ~2.0 ns/op
- **HTTP Request:** ~100-200 µs (local)

## Monitoring

### Logs

View logs in real-time:
```bash
# Development (console format)
LOG_ENCODING=console go run cmd/server/main.go

# Production (JSON format)
./bin/calculator-server | jq '.'
```

### Metrics

Check metrics:
```bash
curl http://localhost:8200/metrics | jq '.'
```

Response:
```json
{
  "active_connections": 5,
  "timestamp": "2025-12-14T12:00:00Z"
}
```

### Health Checks

```bash
# Simple health check
curl http://localhost:8200/health

# With monitoring tools
watch -n 5 'curl -s http://localhost:8200/health | jq .'
```

### Log Analysis

**Find errors:**
```bash
grep -i error server.log
```

**Count requests by method:**
```bash
cat server.log | jq -r '.method' | sort | uniq -c
```

**Calculate average response time:**
```bash
cat server.log | jq -r '.duration_ms' | awk '{sum+=$1; n++} END {print sum/n}'
```

## Production Deployment

### Using Systemd (Linux)

Create `/etc/systemd/system/calculator-server.service`:

```ini
[Unit]
Description=Go Calculator MCP Server
After=network.target

[Service]
Type=simple
User=calculator
WorkingDirectory=/opt/calculator
ExecStart=/opt/calculator/bin/calculator-server
Restart=always
RestartSec=5
Environment=LOG_LEVEL=info
Environment=SERVER_PORT=8200

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable calculator-server
sudo systemctl start calculator-server
sudo systemctl status calculator-server
```

### Using Docker

Build image:
```bash
docker build -t calculator-server .
```

Run container:
```bash
docker run -d \
  --name calculator \
  -p 8200:8200 \
  -e LOG_LEVEL=info \
  --restart unless-stopped \
  calculator-server
```

### Using Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  calculator:
    build: .
    ports:
      - "8200:8200"
    environment:
      - LOG_LEVEL=info
      - SERVER_PORT=8200
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8200/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run:
```bash
docker-compose up -d
```

### Behind Nginx

Nginx configuration:
```nginx
upstream calculator {
    server localhost:8200;
}

server {
    listen 80;
    server_name calculator.example.com;

    location / {
        proxy_pass http://calculator;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # SSE support
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

### SSL/TLS

Use Let's Encrypt with Nginx:
```bash
sudo certbot --nginx -d calculator.example.com
```

## Troubleshooting

### Server Won't Start

**Check port availability:**
```bash
# Linux/Mac
lsof -i :8200

# Windows
netstat -ano | findstr :8200
```

**Check logs:**
```bash
tail -f server.log
```

### High Memory Usage

**Monitor memory:**
```bash
# Linux
ps aux | grep calculator-server

# With continuous monitoring
watch -n 1 'ps aux | grep calculator-server'
```

**Profile memory:**
```bash
go tool pprof http://localhost:8200/debug/pprof/heap
```

### Connection Issues

**Test connectivity:**
```bash
telnet localhost 8200
nc -zv localhost 8200
```

**Check firewall:**
```bash
# Linux
sudo ufw status
sudo iptables -L

# Allow port
sudo ufw allow 8200
```

## Best Practices

1. **Always validate input** on the client side before sending
2. **Handle errors gracefully** in client code
3. **Use connection pooling** for multiple requests
4. **Monitor server health** regularly
5. **Keep logs** for debugging and auditing
6. **Use rate limiting** in client code
7. **Run behind reverse proxy** in production
8. **Enable TLS/HTTPS** for security
9. **Set appropriate timeouts** based on use case
10. **Test with realistic loads** before production

## Support

For issues or questions:
- Check the main [README.md](../README.md)
- Review [example code](../examples/)
- Open an issue on the repository
