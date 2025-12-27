# Observability and Monitoring Implementation Plan

This document outlines a comprehensive plan for implementing observability and monitoring in the py-calculator MCP server using OpenTelemetry and Arize Phoenix.

---

## Executive Summary

Implement a unified observability stack using **OpenTelemetry** as the instrumentation standard and **Arize Phoenix** as the observability backend. This approach ensures:

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
PHOENIX_PROJECT_NAME=py-calculator
PHOENIX_API_KEY=<your-api-key>  # For Phoenix Cloud
```

### 1.2 Define Common Telemetry Standards

Create a shared specification for all MCP tools:

| Attribute | Description | Example |
|-----------|-------------|---------|
| `service.name` | Tool identifier | `py-calculator`, `go-calculator` |
| `service.version` | Semantic version | `0.1.0` |
| `mcp.protocol_version` | MCP protocol version | `2025-03-26` |
| `mcp.session_id` | Client session ID | `a1b2c3d4...` |
| `mcp.method` | JSON-RPC method | `tools/call` |
| `mcp.tool.name` | Tool being invoked | `add`, `divide` |

---

## Phase 2: Python Implementation (py-calculator)

### 2.1 Dependencies

Add to `pyproject.toml`:
```toml
dependencies = [
    "mcp @ git+https://github.com/modelcontextprotocol/python-sdk.git",
    "uvicorn",
    "arize-phoenix>=4.0.0",
    "opentelemetry-sdk>=1.20.0",
    "opentelemetry-exporter-otlp-proto-http>=1.20.0",
    "opentelemetry-instrumentation-fastapi>=0.41b0",
    "openinference-instrumentation>=0.1.0",
]
```

### 2.2 Create Telemetry Module

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

### 2.3 Instrument Calculator Operations

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

### 2.4 Initialize in Server Entry Point

**Add to `calculator/server.py`:**

```python
from calculator.telemetry import initialize_telemetry

# At module level, after imports
initialize_telemetry("py-calculator", "0.1.0")
```

---

## Phase 3: Metrics Collection

### 3.1 Metrics to Collect

| Metric | Type | Description |
|--------|------|-------------|
| `mcp.requests.total` | Counter | Total MCP requests received |
| `mcp.requests.duration` | Histogram | Request duration in milliseconds |
| `mcp.tools.calls` | Counter | Tool invocations by tool name |
| `mcp.tools.errors` | Counter | Tool errors by tool name |
| `mcp.sessions.active` | Gauge | Currently active sessions |

### 3.2 Python Metrics Implementation

**Add to `calculator/telemetry.py`:**

```python
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

def initialize_metrics(service_name: str, version: str) -> None:
    """Initialize OpenTelemetry metrics."""
    endpoint = os.getenv("PHOENIX_METRICS_ENDPOINT", "http://localhost:6006/v1/metrics")

    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: version,
    })

    exporter = OTLPMetricExporter(endpoint=endpoint)
    reader = PeriodicExportingMetricReader(exporter)
    provider = MeterProvider(resource=resource, metric_readers=[reader])

    metrics.set_meter_provider(provider)

def get_meter(name: str = "py-calculator"):
    """Get a meter instance."""
    return metrics.get_meter(name)

# Global metrics instruments
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
tool_error_counter = meter.create_counter(
    "mcp.tools.errors",
    description="Tool errors"
)
```

### 3.3 Instrument Server with Metrics

**Update tool functions in `calculator/server.py`:**

```python
from calculator.telemetry import tool_call_counter, tool_error_counter
import time

@mcp.tool()
def add(a: float | None = None, b: float | None = None) -> Dict[str, Any]:
    """Add two numbers."""
    start_time = time.time()
    tool_call_counter.add(1, {"tool": "add"})

    if a is None or b is None:
        tool_error_counter.add(1, {"tool": "add", "error": "missing_args"})
        return {"error": "Both numbers are required for addition"}

    try:
        result = calculator.calculate("add", a, b)
        return {"result": result}
    except Exception as e:
        tool_error_counter.add(1, {"tool": "add", "error": type(e).__name__})
        raise
```

---

## Phase 4: Structured Logging Integration

### 4.1 Log Correlation with Traces

**Add to `calculator/telemetry.py`:**

```python
import logging
from opentelemetry import trace

class TraceContextFilter(logging.Filter):
    """Add trace context to log records."""

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

def configure_logging():
    """Configure logging with trace context."""
    logger = logging.getLogger()
    logger.addFilter(TraceContextFilter())

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - '
        '[trace_id=%(trace_id)s span_id=%(span_id)s] - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
```

---

## Phase 5: Dashboard and Alerting

### 5.1 Phoenix Dashboard Panels

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

### 5.2 Alert Rules

| Alert | Condition | Severity |
|-------|-----------|----------|
| High Error Rate | error_rate > 5% for 5min | Critical |
| High Latency | p99_latency > 500ms for 5min | Warning |
| Service Down | no_requests for 2min | Critical |
| Tool Failures | tool_errors > 10/min | Warning |

---

## Phase 6: Implementation Checklist

### Python (py-calculator)
- [x] Add OpenTelemetry dependencies to `pyproject.toml`
- [x] Create `calculator/telemetry.py`
- [x] Instrument calculator operations
- [x] Add tracing to MCP request handlers
- [x] Add metrics collection
- [x] Initialize telemetry in server startup
- [x] Add trace context to logs
- [x] Update environment configuration
- [ ] Write tests for telemetry

### Infrastructure
- [ ] Deploy Phoenix (local Docker or Cloud)
- [ ] Configure OTLP endpoints
- [ ] Set up dashboards
- [ ] Configure alerts
- [ ] Document runbooks

---

## Phase 7: Testing Observability

### 7.1 Verify Trace Propagation

```bash
# Start Phoenix
docker run -p 6006:6006 arizephoenix/phoenix:latest

# Or use pip-installed Phoenix
phoenix serve

# Start py-calculator with tracing
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces uv run calculator/server.py

# Make test request
curl -X POST http://localhost:8100/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"add","arguments":{"a":5,"b":3}}}'

# View traces in Phoenix UI
open http://localhost:6006
```

### 7.2 Validate Metrics

Check that metrics appear in Phoenix:
- Navigate to Metrics tab
- Verify `mcp.requests.total` incrementing
- Check `mcp.tools.calls` by tool name

### 7.3 Performance Testing with Observability

Run k6 performance tests while monitoring in Phoenix:

```bash
# Start Phoenix
phoenix serve

# In another terminal, start the server
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces uv run calculator/server.py

# Run performance tests
cd tests/performance
k6 run load-test.js

# View real-time metrics in Phoenix UI
```

---

## Directory Structure Updates

### py-calculator additions:
```
py-calculator/
├── calculator/
│   ├── __init__.py
│   ├── calculator.py       # Updated with tracing
│   ├── server.py            # Updated with telemetry init
│   └── telemetry.py         # New: OpenTelemetry setup
├── docs/
│   └── obs-mon.md           # This document
├── tests/
│   └── test_telemetry.py    # New: Telemetry tests
└── .env.example             # New: Environment configuration
```

---

## Environment Configuration

### `.env.example`:

```env
# Observability Configuration
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces
PHOENIX_METRICS_ENDPOINT=http://localhost:6006/v1/metrics
PHOENIX_PROJECT_NAME=py-calculator
OTEL_SERVICE_NAME=py-calculator
OTEL_TRACES_SAMPLER=always_on
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp

# Optional: Phoenix Cloud
# PHOENIX_API_KEY=your-api-key-here
# PHOENIX_ENDPOINT=https://app.phoenix.arize.com/v1/traces
```

---

## Integration with Performance Testing

The observability implementation integrates seamlessly with the existing k6 performance tests:

1. **Real-time Monitoring**: View request rates, latencies, and errors in Phoenix while tests run
2. **Trace Analysis**: Drill down into individual request traces to identify bottlenecks
3. **Metrics Correlation**: Correlate k6 metrics with OpenTelemetry metrics for comprehensive analysis
4. **Error Investigation**: Use distributed tracing to investigate errors during load tests

---

## References

- [Arize Phoenix Documentation](https://arize.com/docs/phoenix)
- [OpenTelemetry Python SDK](https://opentelemetry.io/docs/languages/python/)
- [OpenTelemetry Python Instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/)
- [Phoenix GitHub Repository](https://github.com/Arize-AI/phoenix)
- [MCP Protocol Specification](https://github.com/modelcontextprotocol)

---

## Version History

- **1.0.0**: Initial observability and monitoring plan for py-calculator

---

*End of Observability and Monitoring Plan*
