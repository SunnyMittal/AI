"""Integration tests for end-to-end chat flow.

NOTE: These tests require:
1. Calculator MCP server running at MCP_SERVER_URL (default: http://127.0.0.1:8000/mcp)
2. Ollama running with llama3.1:8b model
"""

import pytest

from app.config import get_settings
from app.infrastructure.mcp_client import HttpMCPClient
from app.infrastructure.ollama_client import OllamaClientImpl
from app.infrastructure.tool_registry import ToolRegistry
from app.services.chat_service import ChatService
from app.services.conversation_manager import ConversationManager


@pytest.fixture
async def chat_service():
    """Create and initialize a chat service for testing."""
    settings = get_settings()

    mcp_client = HttpMCPClient(
        server_url=settings.mcp_server_url,
    )

    ollama_client = OllamaClientImpl(
        host=settings.ollama_host,
        model=settings.ollama_model,
    )

    tool_registry = ToolRegistry()
    conversation_manager = ConversationManager()

    service = ChatService(
        mcp_client=mcp_client,
        ollama_client=ollama_client,
        tool_registry=tool_registry,
        conversation_manager=conversation_manager,
    )

    await service.initialize()

    yield service

    await service.shutdown()


@pytest.mark.asyncio
async def test_simple_addition(chat_service):
    """Test a simple addition calculation."""
    response_chunks = []

    async for chunk in chat_service.process_message("What is 10 + 5?"):
        response_chunks.append(chunk)

    full_response = "".join(response_chunks)

    assert "15" in full_response or "fifteen" in full_response.lower()


@pytest.mark.asyncio
async def test_multiplication(chat_service):
    """Test multiplication calculation."""
    response_chunks = []

    async for chunk in chat_service.process_message("Calculate 7 times 8"):
        response_chunks.append(chunk)

    full_response = "".join(response_chunks)

    assert "56" in full_response or "fifty" in full_response.lower()


@pytest.mark.asyncio
async def test_division(chat_service):
    """Test division calculation."""
    response_chunks = []

    async for chunk in chat_service.process_message("Divide 100 by 5"):
        response_chunks.append(chunk)

    full_response = "".join(response_chunks)

    assert "20" in full_response or "twenty" in full_response.lower()


@pytest.mark.asyncio
async def test_subtraction(chat_service):
    """Test subtraction calculation."""
    response_chunks = []

    async for chunk in chat_service.process_message("What is 50 minus 23?"):
        response_chunks.append(chunk)

    full_response = "".join(response_chunks)

    assert "27" in full_response


@pytest.mark.asyncio
async def test_division_by_zero(chat_service):
    """Test division by zero error handling."""
    response_chunks = []

    async for chunk in chat_service.process_message("Divide 10 by 0"):
        response_chunks.append(chunk)

    full_response = "".join(response_chunks)

    assert "error" in full_response.lower() or "cannot" in full_response.lower()


@pytest.mark.asyncio
async def test_conversation_context(chat_service):
    """Test that conversation context is maintained."""
    response1_chunks = []
    async for chunk in chat_service.process_message("What is 5 + 3?"):
        response1_chunks.append(chunk)

    history = chat_service.get_conversation_history()
    assert len(history) >= 2


@pytest.mark.asyncio
async def test_clear_conversation(chat_service):
    """Test clearing conversation history."""
    async for _ in chat_service.process_message("What is 1 + 1?"):
        pass

    chat_service.clear_conversation()
    history = chat_service.get_conversation_history()

    assert len(history) == 0
