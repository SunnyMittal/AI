# Observability and Monitoring Implementation Plan

This document outlines a comprehensive plan for implementing consistent observability and monitoring across all MCP server tools, regardless of the programming language used (Python, Go, etc.).

---

## Executive Summary

Implement a unified observability stack using **OpenTelemetry** as the common instrumentation standard and **Arize Phoenix** as the observability backend. This approach ensures:

- Language-agnostic telemetry collection
- Consistent trace correlation across services
- Unified dashboards and alerting
- Minimal code changes per service

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MCP Tool Servers                                 │
├─────────────────────┬─────────────────────┬─────────────────────────────┤
│   py-calculator     │   go-calculator     │   future-tools (any lang)   │
│   (Python)          │   (Go)              │                             │
├─────────────────────┴─────────────────────┴─────────────────────────────┤
│                    OpenTelemetry SDK (per language)                      │
│           Traces │ Metrics │ Logs → OTLP Exporter                       │
├─────────────────────────────────────────────────────────────────────────┤
│                         OTLP Collector (Optional)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                         Arize Phoenix Backend                            │
│              (Traces, Evaluations, Dashboards, Alerting)                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation Setup

### 1.1 Deploy Arize Phoenix

**Option A: Local Development (executable)**

Ref: https://arize.com/docs/phoenix/get-started#run-phoenix-through-your-terminal
```powershell
pip install arize-phoenix
phoenix serve
```

**Option B: Local Development (Docker)**
```bash
docker run -p 6006:6006 arizephoenix/phoenix:latest
```

**Option C: Phoenix Cloud**
- Sign up at https://app.phoenix.arize.com
- Obtain API key and endpoint

**Environment Variables (Common)**
```env
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces
PHOENIX_PROJECT_NAME=go-calculator
PHOENIX_API_KEY=<your-api-key>  # For Phoenix Cloud
```

### 1.2 Define Common Telemetry Standards

Create a shared specification for all MCP tools:

| Attribute | Description | Example |
|-----------|-------------|---------|
| `service.name` | Tool identifier | `go-calculator`, `py-calculator` |
| `service.version` | Semantic version | `1.0.0` |
| `mcp.protocol_version` | MCP protocol version | `2025-03-26` |
| `mcp.session_id` | Client session ID | `a1b2c3d4...` |
| `mcp.method` | JSON-RPC method | `tools/call` |
| `mcp.tool.name` | Tool being invoked | `add`, `divide` |

---

## Phase 2: Go Implementation (go-calculator)

### 2.1 Dependencies

Add to `go.mod`:
```go
go get go.opentelemetry.io/otel
go get go.opentelemetry.io/otel/sdk
go get go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp
go get go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp
```

### 2.2 Create Telemetry Package

**New file: `internal/telemetry/telemetry.go`**

```go
package telemetry

import (
    "context"
    "os"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
    "go.opentelemetry.io/otel/sdk/resource"
    "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.24.0"
)

func Initialize(ctx context.Context, serviceName, version string) (func(), error) {
    endpoint := os.Getenv("PHOENIX_ENDPOINT")
    if endpoint == "" {
        endpoint = "http://localhost:6006/v1/traces"
    }

    exporter, err := otlptracehttp.New(ctx,
        otlptracehttp.WithEndpoint(endpoint),
        otlptracehttp.WithInsecure(),
    )
    if err != nil {
        return nil, err
    }

    res, err := resource.New(ctx,
        resource.WithAttributes(
            semconv.ServiceName(serviceName),
            semconv.ServiceVersion(version),
            attribute.String("mcp.protocol_version", "2025-03-26"),
        ),
    )
    if err != nil {
        return nil, err
    }

    tp := trace.NewTracerProvider(
        trace.WithBatcher(exporter),
        trace.WithResource(res),
    )
    otel.SetTracerProvider(tp)

    cleanup := func() {
        _ = tp.Shutdown(ctx)
    }

    return cleanup, nil
}
```

### 2.3 Instrument HTTP Server

**Modify `internal/mcp/transport.go`:**

```go
import "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"

// Wrap the handler with OpenTelemetry instrumentation
func (t *Transport) Handler() http.Handler {
    return otelhttp.NewHandler(t, "mcp-server")
}
```

### 2.4 Instrument Tool Calls

**Modify `internal/mcp/server.go`:**

```go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/trace"
)

var tracer = otel.Tracer("go-calculator")

func (s *Server) handleToolsCall(ctx context.Context, req *JSONRPCRequest) *JSONRPCResponse {
    ctx, span := tracer.Start(ctx, "tools/call",
        trace.WithAttributes(
            attribute.String("mcp.method", "tools/call"),
        ),
    )
    defer span.End()

    var params ToolCallParams
    if err := json.Unmarshal(req.Params, &params); err != nil {
        span.RecordError(err)
        // ... error handling
    }

    // Add tool-specific attributes
    span.SetAttributes(
        attribute.String("mcp.tool.name", params.Name),
        attribute.Float64("mcp.tool.arg.a", a),
        attribute.Float64("mcp.tool.arg.b", b),
    )

    result, err := s.executeTool(ctx, params.Name, a, b)
    if err != nil {
        span.RecordError(err)
        span.SetAttributes(attribute.Bool("mcp.tool.error", true))
    } else {
        span.SetAttributes(
            attribute.Float64("mcp.tool.result", result),
            attribute.Bool("mcp.tool.error", false),
        )
    }
    // ...
}
```

### 2.5 Update Main Entry Point

**Modify `cmd/server/main.go`:**

```go
import "github.com/mcp/go-calculator/internal/telemetry"

func run() error {
    ctx := context.Background()

    // Initialize telemetry
    cleanup, err := telemetry.Initialize(ctx, "go-calculator", Version)
    if err != nil {
        logger.Warn("failed to initialize telemetry", zap.Error(err))
    } else {
        defer cleanup()
    }

    // ... rest of initialization
}
```

---

## Phase 3: Python Implementation (py-calculator)

### 3.1 Dependencies

Add to `pyproject.toml`:
```toml
dependencies = [
    "mcp @ git+https://github.com/modelcontextprotocol/python-sdk.git",
    "uvicorn",
    "arize-phoenix>=4.0.0",
    "opentelemetry-sdk>=1.20.0",
    "opentelemetry-exporter-otlp>=1.20.0",
    "opentelemetry-instrumentation-fastapi>=0.41b0",
    "openinference-instrumentation>=0.1.0",
]
```

### 3.2 Create Telemetry Module

**New file: `calculator/telemetry.py`**

```python
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION

def initialize_telemetry(service_name: str, version: str) -> None:
    """Initialize OpenTelemetry with Phoenix exporter."""
    endpoint = os.getenv("PHOENIX_ENDPOINT", "http://localhost:6006/v1/traces")

    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: version,
        "mcp.protocol_version": "2025-03-26",
    })

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=endpoint)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

def get_tracer(name: str = "py-calculator"):
    """Get a tracer instance."""
    return trace.get_tracer(name)
```

### 3.3 Instrument Calculator Operations

**Modify `calculator/calculator.py`:**

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer("py-calculator")

class Calculator:
    """Calculator class that manages operations."""

    def __init__(self):
        self._operations: Dict[str, Operation] = {
            'add': Addition(),
            'subtract': Subtraction(),
            'multiply': Multiplication(),
            'divide': Division()
        }

    def calculate(self, operation: str, a: Number, b: Number) -> Number:
        """Perform the specified calculation with tracing."""
        with tracer.start_as_current_span("tools/call") as span:
            span.set_attribute("mcp.method", "tools/call")
            span.set_attribute("mcp.tool.name", operation)
            span.set_attribute("mcp.tool.arg.a", float(a))
            span.set_attribute("mcp.tool.arg.b", float(b))

            if operation not in self._operations:
                span.set_status(Status(StatusCode.ERROR))
                span.record_exception(ValueError(f"Unknown operation: {operation}"))
                raise ValueError(f"Unknown operation: {operation}")

            try:
                result = self._operations[operation].execute(a, b)
                span.set_attribute("mcp.tool.result", float(result))
                span.set_attribute("mcp.tool.error", False)
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR))
                span.record_exception(e)
                span.set_attribute("mcp.tool.error", True)
                raise
```

### 3.4 Initialize in Server Entry Point

**Add to server initialization:**

```python
from calculator.telemetry import initialize_telemetry

# At startup
initialize_telemetry("py-calculator", "0.1.0")
```

---

## Phase 4: Common Metrics

### 4.1 Metrics to Collect

| Metric | Type | Description |
|--------|------|-------------|
| `mcp.requests.total` | Counter | Total MCP requests received |
| `mcp.requests.duration` | Histogram | Request duration in milliseconds |
| `mcp.tools.calls` | Counter | Tool invocations by tool name |
| `mcp.tools.errors` | Counter | Tool errors by tool name |
| `mcp.sessions.active` | Gauge | Currently active sessions |

### 4.2 Go Metrics Implementation

```go
import (
    "go.opentelemetry.io/otel/metric"
)

var (
    requestCounter  metric.Int64Counter
    requestDuration metric.Float64Histogram
    toolCallCounter metric.Int64Counter
)

func initMetrics(meter metric.Meter) {
    requestCounter, _ = meter.Int64Counter("mcp.requests.total",
        metric.WithDescription("Total MCP requests"))
    requestDuration, _ = meter.Float64Histogram("mcp.requests.duration",
        metric.WithDescription("Request duration in ms"))
    toolCallCounter, _ = meter.Int64Counter("mcp.tools.calls",
        metric.WithDescription("Tool invocations"))
}
```

### 4.3 Python Metrics Implementation

```python
from opentelemetry import metrics

meter = metrics.get_meter("py-calculator")

request_counter = meter.create_counter(
    "mcp.requests.total",
    description="Total MCP requests"
)
request_duration = meter.create_histogram(
    "mcp.requests.duration",
    description="Request duration in ms"
)
tool_call_counter = meter.create_counter(
    "mcp.tools.calls",
    description="Tool invocations"
)
```

---

## Phase 5: Structured Logging Integration

### 5.1 Log Correlation with Traces

**Go (zap logger enhancement):**

```go
import "go.opentelemetry.io/otel/trace"

func logWithTrace(ctx context.Context, msg string, fields ...zap.Field) {
    span := trace.SpanFromContext(ctx)
    if span.SpanContext().IsValid() {
        fields = append(fields,
            zap.String("trace_id", span.SpanContext().TraceID().String()),
            zap.String("span_id", span.SpanContext().SpanID().String()),
        )
    }
    logger.Info(msg, fields...)
}
```

**Python:**

```python
import logging
from opentelemetry import trace

class TraceContextFilter(logging.Filter):
    def filter(self, record):
        span = trace.get_current_span()
        if span.is_recording():
            ctx = span.get_span_context()
            record.trace_id = format(ctx.trace_id, '032x')
            record.span_id = format(ctx.span_id, '016x')
        else:
            record.trace_id = "0" * 32
            record.span_id = "0" * 16
        return True
```

---

## Phase 6: Dashboard and Alerting

### 6.1 Phoenix Dashboard Panels

Create dashboards in Phoenix UI for:

1. **Service Overview**
   - Request rate by service
   - Error rate by service
   - P50/P95/P99 latency

2. **Tool Performance**
   - Tool invocation counts
   - Tool latency distribution
   - Tool error rates

3. **Session Analysis**
   - Active sessions over time
   - Session duration distribution
   - Requests per session

### 6.2 Alert Rules

| Alert | Condition | Severity |
|-------|-----------|----------|
| High Error Rate | error_rate > 5% for 5min | Critical |
| High Latency | p99_latency > 500ms for 5min | Warning |
| Service Down | no_requests for 2min | Critical |
| Tool Failures | tool_errors > 10/min | Warning |

---

## Phase 7: Implementation Checklist

### Go (go-calculator)
- [ ] Add OpenTelemetry dependencies to `go.mod`
- [ ] Create `internal/telemetry/telemetry.go`
- [ ] Instrument HTTP server with `otelhttp`
- [ ] Add tracing to `handleToolsCall`
- [ ] Add tracing to `handleInitialize`
- [ ] Add metrics collection
- [ ] Update `main.go` with telemetry initialization
- [ ] Add trace context to structured logs
- [ ] Update `.env.example` with Phoenix config
- [ ] Write tests for telemetry

### Python (py-calculator)
- [ ] Add OpenTelemetry dependencies to `pyproject.toml`
- [ ] Create `calculator/telemetry.py`
- [ ] Instrument calculator operations
- [ ] Add tracing to MCP request handlers
- [ ] Add metrics collection
- [ ] Initialize telemetry in server startup
- [ ] Add trace context to logs
- [ ] Update environment configuration
- [ ] Write tests for telemetry

### Infrastructure
- [ ] Deploy Phoenix (local Docker or Cloud)
- [ ] Configure OTLP endpoints
- [ ] Set up dashboards
- [ ] Configure alerts
- [ ] Document runbooks

---

## Phase 8: Testing Observability

### 8.1 Verify Trace Propagation

```bash
# Start Phoenix
docker run -p 6006:6006 arizephoenix/phoenix:latest

# Start go-calculator with tracing
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces go run cmd/server/main.go

# Make test request
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{...}}'

# View traces in Phoenix UI
open http://localhost:6006
```

### 8.2 Validate Metrics

Check that metrics appear in Phoenix:
- Navigate to Metrics tab
- Verify `mcp.requests.total` incrementing
- Check `mcp.tools.calls` by tool name

---

## Directory Structure Updates

### go-calculator additions:
```
go-calculator/
├── internal/
│   └── telemetry/
│       ├── telemetry.go      # OpenTelemetry setup
│       ├── metrics.go        # Metrics definitions
│       └── telemetry_test.go # Tests
```

### py-calculator additions:
```
py-calculator/
├── calculator/
│   ├── telemetry.py         # OpenTelemetry setup
│   └── ...
```

---

## Environment Configuration

### Common `.env` additions:

```env
# Observability Configuration
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces
PHOENIX_PROJECT_NAME=go-calculator
OTEL_SERVICE_NAME=go-calculator  # or py-calculator
OTEL_TRACES_SAMPLER=always_on
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp

# Optional: Phoenix Cloud
PHOENIX_API_KEY=your-api-key-here
```

---

## References

- [Arize Phoenix Documentation](https://arize.com/docs/phoenix)
- [OpenTelemetry Go Getting Started](https://opentelemetry.io/docs/languages/go/getting-started/)
- [OpenTelemetry Go HTTP Instrumentation](https://pkg.go.dev/go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp)
- [OpenTelemetry Python SDK](https://opentelemetry.io/docs/languages/python/)
- [Phoenix GitHub Repository](https://github.com/Arize-AI/phoenix)

---

## Version History

- **1.0.0**: Initial observability and monitoring plan

---

*End of Observability and Monitoring Plan*
