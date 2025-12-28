# Ollama Client Telemetry with Phoenix

This document describes the OpenTelemetry instrumentation for the Ollama LLM client, providing observability through Arize Phoenix for monitoring, debugging, and analyzing LLM interactions.

---

## Table of Contents

- [Overview](#overview)
- [What is Phoenix?](#what-is-phoenix)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Instrumented Operations](#instrumented-operations)
- [Span Attributes](#span-attributes)
- [Setup Guide](#setup-guide)
- [Viewing Traces](#viewing-traces)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Overview

The MCP client includes built-in OpenTelemetry instrumentation for all Ollama LLM operations. This provides:

- **Real-time monitoring** of LLM requests and responses
- **Performance metrics** including latency, token usage, and throughput
- **Error tracking** with full exception details and stack traces
- **Tool usage analytics** showing which MCP tools are being called
- **Conversation flow visualization** for debugging multi-turn interactions
- **Cost optimization** through token usage analysis

All telemetry data is exported to [Arize Phoenix](https://phoenix.arize.com/), an open-source LLM observability platform.

---

## What is Phoenix?

**Arize Phoenix** is an open-source observability platform specifically designed for LLM applications. It provides:

- 📊 **Trace visualization**: See the complete flow of LLM calls, tool executions, and responses
- 📈 **Performance dashboards**: Monitor latency, token usage, and error rates
- 🔍 **Debugging tools**: Inspect individual requests and responses
- 📉 **Analytics**: Identify patterns, bottlenecks, and optimization opportunities
- 🆓 **Self-hosted**: Run locally with no external dependencies or data sharing

Phoenix uses the OpenTelemetry standard, making it compatible with the broader observability ecosystem.

**Links:**
- Phoenix GitHub: https://github.com/Arize-ai/phoenix
- Documentation: https://docs.arize.com/phoenix
- OpenTelemetry: https://opentelemetry.io/

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │         InstrumentedOllamaClient                   │     │
│  │  - chat_with_tools()                               │     │
│  │  - chat_streaming()                                │     │
│  │  - verify_connection()                             │     │
│  └────────────────┬───────────────────────────────────┘     │
│                   │                                          │
│                   │ Creates spans                            │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────────┐     │
│  │         OpenTelemetry SDK                          │     │
│  │  - TracerProvider                                  │     │
│  │  - BatchSpanProcessor                              │     │
│  │  - Resource (service metadata)                     │     │
│  └────────────────┬───────────────────────────────────┘     │
│                   │                                          │
│                   │ Exports via OTLP/HTTP                    │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────────┐     │
│  │         OTLP HTTP Exporter                         │     │
│  │  - Batches spans                                   │     │
│  │  - Sends to Phoenix endpoint                       │     │
│  └────────────────┬───────────────────────────────────┘     │
└────────────────────┼───────────────────────────────────────┘
                     │
                     │ HTTP POST /v1/traces
                     ▼
         ┌───────────────────────────┐
         │    Phoenix Server         │
         │  (localhost:6006)         │
         │                           │
         │  - Receives traces        │
         │  - Stores data            │
         │  - Provides UI            │
         └───────────────────────────┘
```

**Key Components:**

1. **InstrumentedOllamaClient** (app/infrastructure/ollama_client_instrumented.py)
   - Wraps the standard Ollama client
   - Creates spans for all operations
   - Captures detailed attributes and metrics

2. **Telemetry Module** (app/infrastructure/telemetry.py)
   - Initializes OpenTelemetry SDK
   - Configures Phoenix exporter
   - Provides helper functions for span creation

3. **Dependency Injection** (app/api/dependencies.py)
   - Initializes telemetry on application startup
   - Manages singleton instances
   - Ensures graceful shutdown

---

## Quick Start

### 1. Install Phoenix

```bash
pip install arize-phoenix
```

### 2. Start Phoenix Server

In a separate terminal:

```bash
python -m phoenix.server.main serve
```

Phoenix will start on `http://localhost:6006`

### 3. Configure Environment

Add to your `.env` file:

```env
# OpenTelemetry Configuration
OTEL_SERVICE_NAME=ollama-client
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces
PHOENIX_PROJECT_NAME=calculator-frontend
ENVIRONMENT=development
SERVICE_VERSION=1.0.0
```

### 4. Start the Application

```bash
uvicorn app.api.main:app --reload --port 8001
```

### 5. View Traces

Open http://localhost:6006 in your browser to see real-time traces.

---

## Configuration

All telemetry configuration is done through environment variables.

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OTEL_SERVICE_NAME` | Service identifier in Phoenix | `ollama-client` | No |
| `PHOENIX_ENDPOINT` | Phoenix OTLP endpoint URL | `http://localhost:6006/v1/traces` | No |
| `PHOENIX_PROJECT_NAME` | Project name for trace classification | `default` | No |
| `ENVIRONMENT` | Deployment environment | `development` | No |
| `SERVICE_VERSION` | Application version | `1.0.0` | No |

### Example Configurations

**Development (Local Phoenix):**
```env
OTEL_SERVICE_NAME=calculator-client-dev
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces
PHOENIX_PROJECT_NAME=calculator-frontend
ENVIRONMENT=development
SERVICE_VERSION=1.0.0
```

**Production (Remote Phoenix):**
```env
OTEL_SERVICE_NAME=calculator-client-prod
PHOENIX_ENDPOINT=https://phoenix.yourcompany.com/v1/traces
PHOENIX_PROJECT_NAME=calculator-production
ENVIRONMENT=production
SERVICE_VERSION=2.1.3
```

**Multiple Projects:**

You can separate traces by project using different `PHOENIX_PROJECT_NAME` values:
- `calculator-frontend` - Web client traces
- `calculator-api` - Backend API traces
- `calculator-load-test` - Performance testing traces

---

## Instrumented Operations

### 1. Connection Verification

**Operation:** `ollama.verify_connection`

Executed during application startup to verify Ollama connectivity and model availability.

**Span Name:** `ollama.verify_connection`

**Captured Data:**
- Available models list
- Model verification status
- Connection duration
- Error details if connection fails

**Example:**
```python
await instrumented_client.verify_connection()
```

---

### 2. Chat with Tools (Non-Streaming)

**Operation:** `ollama.chat_with_tools`

Standard chat request with tool-calling capability.

**Span Name:** `ollama.chat_with_tools`

**Captured Data:**
- Request details (message count, tool count)
- Last message preview (first 1000 chars)
- Available tool names
- Response content preview
- Tool calls made (if any)
- Token usage (input/output counts)
- Latency metrics (request duration, total duration)

**Example:**
```python
response = await instrumented_client.chat_with_tools(
    messages=[{"role": "user", "content": "What is 5 + 3?"}],
    tools=[...tool_definitions...]
)
```

---

### 3. Chat Streaming

**Operation:** `ollama.chat_streaming`

Streaming chat for real-time response delivery.

**Span Name:** `ollama.chat_streaming`

**Captured Data:**
- Message count
- Chunk count
- Total content length
- Streaming duration
- Tool call detection flag

**Example:**
```python
async for chunk in await instrumented_client.chat_streaming(
    messages=[{"role": "user", "content": "Calculate 10 * 7"}],
    tools=[...tool_definitions...]
):
    print(chunk)
```

---

## Span Attributes

All spans include semantic conventions following OpenTelemetry and LLM-specific standards.

### Standard Attributes

These attributes are set on **all** Ollama operation spans:

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `llm.vendor` | string | LLM provider | `"ollama"` |
| `llm.model` | string | Model identifier | `"llama3.1:8b"` |
| `llm.operation` | string | Operation type | `"chat_with_tools"` |
| `llm.message_count` | int | Number of messages in conversation | `5` |
| `llm.tool_count` | int | Number of available tools | `4` |
| `llm.host` | string | Ollama server URL | `"http://localhost:11434"` |

### Request Attributes

Set during chat operations:

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `llm.last_message_role` | string | Role of last message | `"user"` |
| `llm.last_message_length` | int | Character count | `42` |
| `llm.last_message_preview` | string | First 1000 chars | `"What is 5 + 3?"` |
| `llm.available_tools` | string (JSON) | Tool names list | `["add", "subtract", ...]` |

### Response Attributes

Set after receiving LLM response:

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `llm.response_length` | int | Response character count | `125` |
| `llm.response_preview` | string | First 1000 chars of response | `"The sum of 5 and 3 is 8."` |
| `llm.tool_calls_count` | int | Number of tool calls made | `1` |
| `llm.called_tools` | string (JSON) | Names of called tools | `["add"]` |

### Token Usage Attributes

Token counts from Ollama response:

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `llm.tokens_input` | int | Prompt tokens consumed | `234` |
| `llm.tokens_output` | int | Completion tokens generated | `67` |

### Performance Attributes

Timing and performance metrics:

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `llm.duration_ms` | float | Request duration (wall clock) | `1543.23` |
| `llm.total_duration_ms` | float | Total Ollama processing time | `1521.45` |

### Streaming-Specific Attributes

Only set for streaming operations:

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `llm.chunk_count` | int | Number of chunks received | `23` |
| `llm.total_content_length` | int | Total characters streamed | `456` |
| `llm.has_tool_calls` | bool | Whether tool calls were detected | `true` |

### Connection Verification Attributes

Only set during `verify_connection`:

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `llm.available_models_count` | int | Number of models available | `5` |

### Error Attributes

Set when operations fail:

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `span.status` | enum | Span status code | `ERROR` |
| `span.status_message` | string | Error description | `"Failed to connect to Ollama"` |
| `exception.type` | string | Exception class name | `"OllamaError"` |
| `exception.message` | string | Exception message | `"Connection refused"` |
| `exception.stacktrace` | string | Full stack trace | `"Traceback..."` |

---

## Setup Guide

### Installation

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

This installs:
- `opentelemetry-api>=1.20.0`
- `opentelemetry-sdk>=1.20.0`
- `opentelemetry-exporter-otlp-proto-http>=1.20.0`

2. **Install Phoenix:**

```bash
pip install arize-phoenix
```

Or via Docker:

```bash
docker pull arizephoenix/phoenix:latest
docker run -p 6006:6006 arizephoenix/phoenix:latest
```

### Configuration

1. **Copy environment template:**

```bash
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

2. **Configure telemetry settings in `.env`:**

```env
# OpenTelemetry Configuration
OTEL_SERVICE_NAME=ollama-client
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces
PHOENIX_PROJECT_NAME=calculator-frontend
ENVIRONMENT=development
SERVICE_VERSION=1.0.0
```

3. **Start Phoenix:**

```bash
python -m phoenix.server.main serve
```

4. **Verify Phoenix is running:**

Open http://localhost:6006 in your browser.

### Enabling Telemetry

Telemetry is **automatically enabled** when the application starts. The initialization happens in `app/api/dependencies.py`:

```python
from app.infrastructure.telemetry import initialize_telemetry

# Called during application startup
initialize_telemetry()
```

No code changes are needed. Simply configure the environment variables and telemetry will work.

### Disabling Telemetry

To disable telemetry (e.g., for testing), set an invalid Phoenix endpoint:

```env
PHOENIX_ENDPOINT=http://disabled:9999/v1/traces
```

The application will continue to work normally, but traces won't be exported. A warning will be logged.

---

## Viewing Traces

### Phoenix UI Overview

1. **Open Phoenix:** http://localhost:6006

2. **Projects Tab:** Select your project (e.g., `calculator-frontend`)

3. **Traces Tab:** View all traces in real-time

### Trace Details

Click on any trace to see:

- **Span timeline:** Visual representation of operation duration
- **Attributes:** All captured metadata (request, response, performance)
- **Events:** Exception details and errors
- **Context:** Service info, environment, version

### Useful Filters

**Filter by operation:**
```
llm.operation = "chat_with_tools"
```

**Filter by model:**
```
llm.model = "llama3.1:8b"
```

**Filter by errors:**
```
span.status = "ERROR"
```

**Filter by tool usage:**
```
llm.tool_calls_count > 0
```

**Filter by slow requests:**
```
llm.duration_ms > 2000
```

### Example Trace Flow

A typical conversation trace looks like:

```
ollama.verify_connection (startup)
  └─ Duration: 245ms
  └─ Status: OK
  └─ Available models: 5

ollama.chat_with_tools (user: "What is 5 + 3?")
  └─ Duration: 1543ms
  └─ Messages: 1
  └─ Tools: 4
  └─ Tool calls: 1 (add)
  └─ Tokens: 234 in, 67 out
  └─ Response: "I'll add those numbers..."

ollama.chat_with_tools (tool result processing)
  └─ Duration: 892ms
  └─ Messages: 3
  └─ Tools: 4
  └─ Response: "The sum of 5 and 3 is 8."
```

---

## Troubleshooting

### Issue: Traces not appearing in Phoenix

**Symptoms:**
- Phoenix UI shows no traces
- Application runs normally

**Solutions:**

1. **Verify Phoenix is running:**
   ```bash
   curl http://localhost:6006
   ```
   Should return Phoenix UI HTML.

2. **Check endpoint configuration:**
   ```env
   PHOENIX_ENDPOINT=http://localhost:6006/v1/traces
   ```
   Note: Must end with `/v1/traces`, not just `/`

3. **Check application logs:**
   Look for telemetry initialization message:
   ```
   INFO: Telemetry initialized: service=ollama-client, project=calculator-frontend, endpoint=http://localhost:6006/v1/traces, env=development
   ```

4. **Test OTLP endpoint:**
   ```bash
   curl -X POST http://localhost:6006/v1/traces \
     -H "Content-Type: application/json" \
     -d '{}'
   ```

---

### Issue: "Failed to initialize telemetry" warning

**Symptoms:**
- Warning in logs: `Failed to initialize telemetry: [error]. Continuing without tracing.`
- Application continues to work

**Cause:**
- Phoenix not running
- Invalid endpoint configuration
- Network connectivity issues

**Solution:**
- This is a **non-fatal error** - the application uses a no-op tracer
- Start Phoenix and restart the application
- Verify `PHOENIX_ENDPOINT` is correct

---

### Issue: High overhead/performance impact

**Symptoms:**
- Slow LLM requests
- High memory usage

**Solutions:**

1. **Batch span processor** (already configured):
   - Spans are batched before export
   - Default: 512 spans per batch
   - Default: 5-second export interval

2. **Reduce attribute verbosity:**

   Edit `app/infrastructure/ollama_client_instrumented.py`:
   ```python
   # Comment out preview attributes to reduce size
   # span.set_attribute("llm.last_message_preview", content[:1000])
   # span.set_attribute("llm.response_preview", content[:1000])
   ```

3. **Sampling** (for high-volume scenarios):

   Edit `app/infrastructure/telemetry.py`:
   ```python
   from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

   provider = TracerProvider(
       resource=resource,
       sampler=TraceIdRatioBased(0.5)  # Sample 50% of traces
   )
   ```

---

### Issue: Missing attributes

**Symptoms:**
- Some attributes don't appear in Phoenix
- Attributes show as `null`

**Causes & Solutions:**

1. **Ollama doesn't return token counts:**
   - Token usage attributes (`llm.tokens_input`, `llm.tokens_output`) are only available if Ollama returns them
   - Not all models provide this data

2. **Empty tool calls:**
   - `llm.tool_calls_count` and `llm.called_tools` only appear when tools are actually called
   - Normal for direct responses

3. **Streaming-specific attributes:**
   - `llm.chunk_count` only appears for `chat_streaming` operations
   - Not available for standard `chat_with_tools`

---

## Best Practices

### 1. Use Descriptive Project Names

Organize traces by environment and component:

```env
# Development
PHOENIX_PROJECT_NAME=calculator-frontend-dev

# Staging
PHOENIX_PROJECT_NAME=calculator-frontend-staging

# Production
PHOENIX_PROJECT_NAME=calculator-frontend-prod
```

### 2. Tag Deployments with Versions

Update `SERVICE_VERSION` when deploying:

```env
SERVICE_VERSION=2.1.0
```

This helps correlate performance changes with specific releases.

### 3. Monitor Key Metrics

Set up Phoenix dashboards to track:

- **95th percentile latency:** Detect performance degradation
- **Error rate:** Monitor `span.status = ERROR`
- **Tool usage:** Identify most-used MCP tools
- **Token consumption:** Optimize costs

### 4. Investigate Slow Requests

Use Phoenix to find slow traces:

1. Filter: `llm.duration_ms > 5000`
2. Examine attributes: message length, tool count, token usage
3. Optimize: simplify prompts, reduce tool count, or adjust model

### 5. Debug Tool Call Issues

When tool calls fail:

1. Find the trace in Phoenix
2. Check `llm.called_tools` - was the right tool selected?
3. Check `llm.response_preview` - did the LLM explain the error?
4. Check exception details for MCP errors

### 6. Archive Historical Data

Phoenix stores traces in-memory by default. For long-term storage:

- Use Phoenix with persistent storage (PostgreSQL backend)
- Export critical traces for postmortem analysis
- Set up retention policies

### 7. Respect Privacy

Be careful with sensitive data in traces:

- Message content is captured in `llm.last_message_preview` and `llm.response_preview`
- Truncated to 1000 characters by default
- Consider filtering PII in production environments

---

## Code Reference

### Key Files

| File | Purpose | Line References |
|------|---------|-----------------|
| `app/infrastructure/telemetry.py` | Telemetry initialization and configuration | All |
| `app/infrastructure/ollama_client_instrumented.py` | Instrumented Ollama client | All |
| `app/api/dependencies.py` | Dependency injection and startup | 10, 46-76, 136-141 |
| `.env.example` | Environment configuration template | 16-21 |
| `requirements.txt` | OpenTelemetry dependencies | 10-13 |

### Integration Points

**Startup (app/api/main.py):**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Telemetry is initialized here via dependencies
    await initialize_services()
    yield
    await shutdown_services()
```

**Client Factory (app/api/dependencies.py:46-76):**
```python
def get_ollama_client(settings: Settings | None = None) -> InstrumentedOllamaClient:
    global _ollama_client, _telemetry_initialized

    if _ollama_client is None:
        if not _telemetry_initialized:
            initialize_telemetry()
            _telemetry_initialized = True

        _ollama_client = InstrumentedOllamaClient(
            host=settings.ollama_host,
            model=settings.ollama_model,
        )

    return _ollama_client
```

---

## Additional Resources

### Phoenix Documentation
- Official Docs: https://docs.arize.com/phoenix
- GitHub: https://github.com/Arize-ai/phoenix
- Quickstart: https://docs.arize.com/phoenix/quickstart

### OpenTelemetry
- Specification: https://opentelemetry.io/docs/specs/
- Python SDK: https://opentelemetry-python.readthedocs.io/
- Semantic Conventions: https://opentelemetry.io/docs/specs/semconv/

### Related Documentation
- MCP Client Architecture: `README.md`
- Regeneration Prompt: `docs/regen.md`
- Setup Guide: `Setup.md`

---

## Summary

The Ollama client telemetry provides comprehensive observability for LLM operations using OpenTelemetry and Phoenix. Key benefits:

✅ **Zero-code instrumentation** - automatically enabled via environment config
✅ **Rich metadata** - captures request/response details, performance, and errors
✅ **Production-ready** - batched exports, graceful degradation, minimal overhead
✅ **Open source** - Phoenix is free and self-hosted
✅ **Standards-based** - uses OpenTelemetry for interoperability

With telemetry enabled, you gain deep visibility into LLM behavior, enabling faster debugging, performance optimization, and better understanding of user interactions.
