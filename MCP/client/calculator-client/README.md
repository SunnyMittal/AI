# Calculator MCP Web Client

A Python-based web client for the Calculator MCP server that uses Ollama's CodeLlama model for intelligent tool selection and provides a modern chat interface for arithmetic operations.

## Features

- **Intelligent Tool Selection**: Uses Ollama's `codellama:34b-instruct` model to determine which calculator operation to execute based on natural language input
- **Real-time Chat Interface**: WebSocket-based streaming responses for a ChatGPT-like experience
- **MCP Integration**: Connects to the Calculator MCP server using the stdio transport
- **SOLID Architecture**: Clean, maintainable code following SOLID principles with dependency injection
- **Async/Await**: Non-blocking architecture for high performance
- **Modern UI**: Responsive, ChatGPT-inspired interface

## Architecture

The application follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────┐
│         Presentation Layer (FastAPI)            │
│  - WebSocket endpoints for real-time chat       │
│  - REST endpoints for health/status             │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│           Service Layer (Business Logic)        │
│  - ChatService: Orchestrates LLM + MCP          │
│  - ConversationManager: Manages chat history    │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│          Infrastructure Layer (Adapters)        │
│  - MCPClientAdapter: MCP server communication   │
│  - OllamaAdapter: LLM integration               │
│  - ToolRegistry: Tool discovery and mapping     │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│              Domain Layer (Core)                │
│  - Message models                               │
│  - Tool schemas                                 │
└─────────────────────────────────────────────────┘
```

## Prerequisites

1. **Python 3.13+**
2. **Calculator MCP Server** at `D:\AI\MCP\server\calculator`
3. **Ollama** installed and running
4. **Tool-compatible Ollama model** - **IMPORTANT**: The model must support function calling. Recommended options:
   - `ollama pull llama3.1:8b` ✅ **Recommended** (best balance of size/performance)
   - `ollama pull llama3.2:3b` ✅ (smaller, faster)
   - `ollama pull mistral` ✅
   - `ollama pull mixtral` ✅
   - ❌ **NOT** `codellama` (does not support tools)

## Installation

### 1. Clone or navigate to the project directory

```bash
cd D:\AI\MCP\client\calculator-client
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac
```

### 3. Install dependencies

Using pip:
```bash
pip install -r requirements.txt
```

Or using the project configuration:
```bash
pip install -e .
```

### 4. Configure environment variables

Copy the example environment file and configure it:

```bash
copy .env.example .env  # On Windows
# cp .env.example .env  # On Linux/Mac
```

Edit `.env` to match your setup:

```env
# MCP Server Configuration
MCP_SERVER_PATH=D:/AI/MCP/server/calculator
MCP_PYTHON_PATH=D:/AI/MCP/server/calculator/.venv/Scripts/python.exe

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=codellama:34b-instruct

# Application Configuration
LOG_LEVEL=INFO
CORS_ORIGINS=*
MAX_CONVERSATION_HISTORY=50
```

## Running the Application

### 1. Start the Calculator MCP Server

In a separate terminal:

```bash
cd D:\AI\MCP\server\calculator
python -m calculator.server
```

### 2. Start Ollama

Ensure Ollama is running:

```bash
ollama serve
```

Verify the model is available:

```bash
ollama list
```

If `codellama:34b-instruct` is not listed, pull it:

```bash
ollama pull codellama:34b-instruct
```

### 3. Start the Web Client

```bash
cd D:\AI\MCP\client\calculator-client
uvicorn app.api.main:app --reload
```

Or run directly:

```bash
python -m app.api.main
```

The application will start on `http://localhost:8000`

## Usage

1. Open your browser and navigate to `http://localhost:8000`
2. You'll see a chat interface with a welcome message
3. Type natural language requests for calculations:
   - "What is 25 + 17?"
   - "Calculate 100 divided by 5"
   - "Multiply 7 and 8"
   - "What's 50 minus 23?"
4. The assistant will use the LLM to determine the appropriate operation and execute it via the MCP server
5. Results stream back in real-time

## API Endpoints

### REST Endpoints

- `GET /` - Redirects to the frontend
- `GET /health` - Health check endpoint
- `GET /tools` - List available MCP tools

### WebSocket Endpoint

- `WS /ws/chat` - Real-time chat with streaming responses

## Testing

### Run Unit Tests

```bash
pytest tests/unit -v
```

### Run Integration Tests

**Note**: Integration tests require the MCP server and Ollama to be running.

```bash
pytest tests/integration -v
```

### Run All Tests

```bash
pytest -v
```

### Run Tests with Coverage

```bash
pytest --cov=app --cov-report=html
```

## Project Structure

```
calculator-client/
├── app/
│   ├── domain/                    # Core business entities
│   │   ├── models.py              # Message, ToolCall, ToolResult
│   │   └── exceptions.py          # Custom exceptions
│   ├── infrastructure/            # External integrations
│   │   ├── mcp_client.py          # MCP SDK adapter
│   │   ├── ollama_client.py       # Ollama integration
│   │   └── tool_registry.py       # Tool management
│   ├── services/                  # Business logic
│   │   ├── chat_service.py        # Main orchestration
│   │   └── conversation_manager.py # History management
│   ├── api/                       # Presentation layer
│   │   ├── main.py                # FastAPI app
│   │   ├── websocket.py           # WebSocket endpoints
│   │   ├── routes.py              # REST endpoints
│   │   └── dependencies.py        # Dependency injection
│   ├── static/                    # Frontend assets
│   │   ├── index.html
│   │   ├── app.js
│   │   └── styles.css
│   └── config.py                  # Configuration
├── tests/
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── fixtures/                  # Test fixtures
├── .env.example                   # Environment template
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

## SOLID Principles

This project demonstrates SOLID principles:

- **Single Responsibility**: Each class has one clear purpose
- **Open/Closed**: Can add new tools/LLM providers without modifying existing code
- **Liskov Substitution**: Protocol-based adapters are interchangeable
- **Interface Segregation**: Minimal protocol interfaces
- **Dependency Inversion**: High-level modules depend on abstractions

## Troubleshooting

### MCP Connection Error

- Verify the MCP server is running
- Check `MCP_SERVER_PATH` and `MCP_PYTHON_PATH` in `.env`
- Ensure the Python path points to the correct virtual environment

### Ollama Error

- Verify Ollama is running: `ollama list`
- Pull a tool-compatible model: `ollama pull llama3.1:8b`
- Check `OLLAMA_HOST` in `.env` matches your Ollama installation

### "Model does not support tools" Error

**Error**: `registry.ollama.ai/library/[model] does not support tools (status code: 400)`

**Cause**: The selected model doesn't support Ollama's function calling feature.

**Solution**:
1. Pull a compatible model: `ollama pull llama3.1:8b`
2. Update `.env`: `OLLAMA_MODEL=llama3.1:8b`
3. Restart the server

**Compatible models**: llama3.1, llama3.2, mistral, mixtral, qwen2.5
**Incompatible models**: codellama, older llama2 versions

### WebSocket Connection Failed

- Check browser console for errors
- Verify CORS settings in `.env`
- Ensure the server is running and accessible

### Tool Execution Errors

- Check MCP server logs for errors
- Verify tool parameters are correctly formatted
- Test the MCP server directly to ensure it's working

## Development

### Code Formatting

```bash
black app tests
```

### Linting

```bash
ruff check app tests
```

### Type Checking

```bash
mypy app
```

## License

This project is part of the MCP ecosystem demonstration.

## Contributing

Contributions are welcome! Please ensure:

1. Code follows SOLID principles
2. Tests are included for new features
3. Code is formatted with Black
4. Type hints are used throughout
5. Documentation is updated

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Uses [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Powered by [Ollama](https://ollama.ai/)
- LLM: CodeLlama 34B Instruct
