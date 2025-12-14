# MCP Client Regeneration Prompt

This document provides a deterministic prompt for regenerating a Python MCP (Model Context Protocol) client with LLM integration. Use this prompt with an AI assistant to recreate the client from scratch.

---

## THE PROMPT

```
Create a Python MCP client web application with the following exact specifications:

## PROJECT OVERVIEW

Build a Python-based web client that:
1. Connects to an MCP server (via HTTP/JSON-RPC or stdio transport)
2. Uses Ollama LLM for intelligent tool selection and natural language processing
3. Provides a modern chat web interface with WebSocket streaming
4. Follows SOLID principles with clean layered architecture

## TECHNOLOGY STACK

- Python 3.13+
- FastAPI (web framework)
- Uvicorn (ASGI server)
- Pydantic 2.x (data validation and settings)
- httpx (async HTTP client for MCP communication)
- mcp SDK (MCP Python SDK for stdio transport option)
- ollama (Ollama client library)
- WebSocket for real-time chat streaming

## DIRECTORY STRUCTURE

Create this exact structure:

```
project-name/
├── app/
│   ├── __init__.py
│   ├── config.py                    # Pydantic Settings configuration
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py                # Domain models (Message, ToolCall, etc.)
│   │   └── exceptions.py            # Custom exception hierarchy
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── mcp_client.py            # MCP client adapters (HTTP + Stdio)
│   │   ├── ollama_client.py         # Ollama LLM integration
│   │   └── tool_registry.py         # Tool discovery and schema transformation
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat_service.py          # Main orchestration service
│   │   └── conversation_manager.py  # Chat history management
│   └── api/
│       ├── __init__.py
│       ├── main.py                  # FastAPI app entry point
│       ├── routes.py                # REST endpoints
│       ├── websocket.py             # WebSocket chat endpoint
│       ├── dependencies.py          # Dependency injection container
│       └── static/
│           ├── index.html           # Chat UI
│           ├── app.js               # Frontend WebSocket logic
│           └── styles.css           # ChatGPT-style UI
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_tool_registry.py
│   │   └── test_conversation_manager.py
│   └── integration/
│       ├── __init__.py
│       └── test_chat_flow.py
├── pyproject.toml
├── requirements.txt
├── .env.example
└── README.md
```

## DEPENDENCIES (pyproject.toml)

```toml
[project]
name = "project-name"
version = "0.1.0"
description = "MCP web client with Ollama LLM integration"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "mcp>=1.0.0",
    "ollama>=0.4.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
    "black>=24.0.0",
    "mypy>=1.8.0",
    "ruff>=0.2.0",
]

[build-system]
requires = ["setuptools>=68.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

## CONFIGURATION (app/config.py)

Use Pydantic Settings with these environment variables:
- MCP_SERVER_URL: HTTP URL for MCP server (default: http://127.0.0.1:8000/mcp)
- OLLAMA_HOST: Ollama API host (default: http://localhost:11434)
- OLLAMA_MODEL: LLM model name (default: llama3.1:8b)
- LOG_LEVEL: Logging level (default: INFO)
- CORS_ORIGINS: CORS allowed origins (default: *)
- MAX_CONVERSATION_HISTORY: Max messages to keep (default: 50)
- PORT: Server port (default: 8001)

## DOMAIN LAYER

### models.py

Create these Pydantic models (all frozen/immutable):

1. **MessageRole** (Enum): USER, ASSISTANT, TOOL

2. **Message**:
   - role: MessageRole
   - content: str
   - timestamp: datetime (auto-set to now)
   - tool_call_id: Optional[str]
   - tool_name: Optional[str]

3. **ToolCall**:
   - id: str
   - name: str
   - arguments: dict[str, Any]

4. **ToolResult**:
   - tool_call_id: str
   - tool_name: str
   - success: bool
   - result: Any
   - error: Optional[str]

5. **ConversationContext**:
   - messages: list[Message]
   - max_history: int
   - Methods: add_message(), get_recent_messages(), clear()

### exceptions.py

Create exception hierarchy:
- CalculatorClientError (base)
  - MCPConnectionError
  - ToolNotFoundError
  - ToolExecutionError
  - OllamaError
  - ConfigurationError

## INFRASTRUCTURE LAYER

### mcp_client.py

**CRITICAL: Implement two MCP client adapters**

1. **MCPClientAdapter Protocol**:
```python
class MCPClientAdapter(Protocol):
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def list_tools(self) -> list[dict[str, Any]]: ...
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...
```

2. **HttpMCPClient** (primary - uses HTTP/JSON-RPC):
   - Implements MCP 2024-11-05 protocol
   - Uses JSON-RPC 2.0 with SSE responses
   - Manages session IDs via mcp-session-id header
   - Methods:
     - initialize: Establish session with protocol negotiation
     - notifications/initialized: Required MCP notification after init
     - tools/list: List available tools
     - tools/call: Execute a tool
   - Parse SSE format responses (lines starting with "data: ")
   - Cache tools list after first fetch

3. **StdioMCPClient** (alternative - uses stdio transport):
   - Uses mcp.ClientSession and StdioServerParameters
   - Spawns subprocess of MCP server
   - Uses AsyncExitStack for resource management

### ollama_client.py

**OllamaAdapter Protocol**:
```python
class OllamaAdapter(Protocol):
    async def chat_with_tools(self, messages: list[dict], tools: list[dict]) -> dict[str, Any]: ...
    async def verify_connection(self) -> None: ...
```

**OllamaClientImpl**:
- Use ollama.AsyncClient
- verify_connection(): Check model exists via client.show()
- chat_with_tools(): Call client.chat() with messages and tools
- Handle connection errors, raise OllamaError

### tool_registry.py

**ToolRegistry class**:
- Store tools as dict[str, dict]
- Methods:
  - register_tool(tool) / register_tools(tools)
  - get_tool(name) - raise ToolNotFoundError if missing
  - get_all_tools() / tool_exists(name)
  - to_ollama_format() - Transform MCP schema to Ollama format
  - clear()

**CRITICAL: Schema transformation**
Transform MCP inputSchema to Ollama parameters format:
```python
def to_ollama_format(self) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": self._transform_input_schema(tool.get("inputSchema", {})),
            },
        }
        for tool in self._tools.values()
    ]
```

## SERVICE LAYER

### conversation_manager.py

**ConversationManager class**:
- Store messages list with configurable max_history
- Methods:
  - add_message(message): Add and trim if exceeds max
  - get_history(limit=None): Get messages
  - to_ollama_format(limit=None): Convert to Ollama message format
  - clear(): Reset history
- Properties: is_empty, __len__

### chat_service.py

**CRITICAL: ChatService class - the core orchestration engine**

Dependencies: MCPClientAdapter, OllamaAdapter, ToolRegistry, ConversationManager

**Methods**:

1. **initialize()**: Connect MCP, discover tools, verify Ollama

2. **shutdown()**: Disconnect MCP

3. **process_message(user_input: str) -> AsyncIterator[str]**:
   - Add user message to conversation
   - Call Ollama with history + tools
   - If tool_calls present: handle via _handle_tool_calls()
   - Else: yield content directly
   - Add assistant message to conversation

4. **_handle_tool_calls(tool_calls: list[dict]) -> AsyncIterator[str]**:
   - Extract tool name and arguments from function dict
   - Parse JSON string arguments if needed
   - **CRITICAL: Coerce numeric arguments** (LLMs return numbers as strings)
   - Call MCP tool
   - Append tool call and result to messages
   - Re-call LLM for final natural language response
   - Yield final response

5. **_coerce_numeric_arguments(arguments: dict) -> dict**:
   ```python
   def _coerce_numeric_arguments(self, arguments: dict) -> dict:
       coerced = {}
       for key, value in arguments.items():
           if isinstance(value, str):
               try:
                   coerced[key] = int(value)
               except ValueError:
                   try:
                       coerced[key] = float(value)
                   except ValueError:
                       coerced[key] = value
           else:
               coerced[key] = value
       return coerced
   ```

## PRESENTATION LAYER

### main.py

FastAPI application setup:
- Lifespan context manager for startup/shutdown
- CORS middleware
- Static file mounting at /static
- Include routes and websocket routers
- Logging configuration

### routes.py

REST endpoints:
- GET / -> Redirect to /static/index.html
- GET /health -> {"status": "healthy", "tools_count": N}
- GET /tools -> {"tools": [...], "count": N}

### websocket.py

**WebSocket endpoint /ws/chat**:
```python
@router.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    chat_service = get_chat_service()
    try:
        while True:
            user_message = await websocket.receive_text()
            async for chunk in chat_service.process_message(user_message):
                await websocket.send_text(chunk)
            await websocket.send_text("[DONE]")  # Signal completion
    except WebSocketDisconnect:
        pass
```

### dependencies.py

**Dependency injection container**:
- Global singletons for services
- Factory functions:
  - get_mcp_client() -> HttpMCPClient (default) or StdioMCPClient
  - get_ollama_client() -> OllamaClientImpl
  - get_tool_registry() -> ToolRegistry (LRU cached)
  - get_conversation_manager() -> ConversationManager (session-scoped)
  - get_chat_service() -> ChatService
- initialize_services() / shutdown_services() for lifespan

## FRONTEND

### index.html

ChatGPT-style layout:
- Header with title and connection status indicator
- Scrollable messages container
- Input field + send button
- Status dot: green=connected, red=disconnected, yellow=reconnecting

### app.js

WebSocket client:
- Dynamic URL based on window.location (http/https support)
- Auto-reconnection with exponential backoff (5 attempts, 2s initial)
- Message rendering: user (blue right), assistant (white left)
- Send on button click or Enter key
- Disable input during processing
- Listen for "[DONE]" marker to re-enable input
- Auto-scroll to bottom

### styles.css

Modern responsive design:
- ChatGPT-inspired colors (blue primary)
- Animations: fadeIn, pulse for status
- Responsive breakpoint at 768px
- Custom scrollbar styling

## CRITICAL IMPLEMENTATION DETAILS

1. **Numeric Coercion**: LLMs return tool arguments as strings. MUST convert to int/float before MCP call.

2. **SSE Parsing**: HTTP MCP responses use SSE format. Parse "data: {...}" lines.

3. **Tool Schema Transformation**: MCP uses inputSchema, Ollama uses parameters.

4. **Conversation Context**: Maintain full history for multi-turn interactions.

5. **Session Management**: HTTP MCP client must track mcp-session-id header.

6. **[DONE] Marker**: WebSocket sends "[DONE]" to signal response completion.

## MESSAGE FLOW

```
User Input (WebSocket)
    ↓
ConversationManager.add_message(user)
    ↓
Ollama.chat_with_tools(history, tools)
    ↓
IF tool_calls:
    MCP.call_tool(name, coerced_args)
    Append tool call + result to messages
    Ollama.chat_with_tools(updated_history)
    ↓
ELSE:
    Direct response
    ↓
ConversationManager.add_message(assistant)
    ↓
Stream chunks to WebSocket
    ↓
Send [DONE]
```

## MCP HTTP PROTOCOL DETAILS

**Initialize sequence**:
```json
POST /mcp
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "client-name", "version": "0.1.0"}
    }
}
```
Response includes mcp-session-id header. Then send:
```json
POST /mcp (with mcp-session-id header)
{"jsonrpc": "2.0", "method": "notifications/initialized"}
```

**List tools**:
```json
POST /mcp (with mcp-session-id header)
{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
```

**Call tool**:
```json
POST /mcp (with mcp-session-id header)
{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {"name": "tool_name", "arguments": {...}}
}
```

## TESTING

Unit tests for:
- ToolRegistry: registration, retrieval, Ollama format conversion
- ConversationManager: add/get/clear, max history trimming

Integration tests (require MCP server + Ollama running):
- End-to-end chat flows
- Tool execution
- Error handling

Pytest configuration:
- asyncio_mode = "auto"
- testpaths = ["tests"]

## ENVIRONMENT FILE (.env.example)

```env
MCP_SERVER_URL=http://127.0.0.1:8000/mcp
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
LOG_LEVEL=INFO
CORS_ORIGINS=*
PORT=8001
MAX_CONVERSATION_HISTORY=50
```

## RUNNING

```bash
pip install -e .
uvicorn app.api.main:app --reload --port 8001
```

Open http://localhost:8001 in browser.

---

Generate all files with complete, production-ready implementations. Follow SOLID principles. Use Protocol-based dependency injection. Handle errors gracefully. Include proper logging throughout.
```

---

## USAGE

Copy the prompt above and provide it to an AI assistant capable of generating code. The prompt contains all necessary specifications to recreate the MCP client deterministically:

1. Exact directory structure
2. All dependencies with versions
3. Complete API specifications
4. Critical implementation details (numeric coercion, SSE parsing, etc.)
5. Protocol definitions for extensibility
6. Frontend specifications
7. Testing structure
8. Configuration management

The resulting application will:
- Connect to any MCP server via HTTP or stdio
- Use Ollama for natural language understanding
- Provide a modern chat interface
- Support tool execution with proper type coercion
- Maintain conversation context
- Handle errors gracefully
