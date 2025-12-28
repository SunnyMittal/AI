"""Dependency injection configuration for FastAPI."""

import logging
from functools import lru_cache
from typing import AsyncGenerator

from app.config import Settings, get_settings
from app.infrastructure.mcp_client import HttpMCPClient, StdioMCPClient
from app.infrastructure.ollama_client_instrumented import InstrumentedOllamaClient
from app.infrastructure.telemetry import initialize_telemetry
from app.infrastructure.tool_registry import ToolRegistry
from app.services.chat_service import ChatService
from app.services.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)

_mcp_client: HttpMCPClient | StdioMCPClient | None = None
_ollama_client: InstrumentedOllamaClient | None = None
_tool_registry: ToolRegistry | None = None
_chat_service: ChatService | None = None
_telemetry_initialized: bool = False


def get_mcp_client(settings: Settings | None = None) -> HttpMCPClient | StdioMCPClient:
    """Get or create the MCP client singleton.

    Args:
        settings: Application settings

    Returns:
        MCP client instance
    """
    global _mcp_client

    if _mcp_client is None:
        if settings is None:
            settings = get_settings()

        # Use HTTP client for the MCP server
        _mcp_client = HttpMCPClient(server_url=settings.mcp_server_url)
        logger.info("Created HTTP MCP client instance")

    return _mcp_client


def get_ollama_client(settings: Settings | None = None) -> InstrumentedOllamaClient:
    """Get or create the instrumented Ollama client singleton.

    Args:
        settings: Application settings

    Returns:
        Instrumented Ollama client instance
    """
    global _ollama_client, _telemetry_initialized

    if _ollama_client is None:
        if settings is None:
            settings = get_settings()

        # Initialize telemetry if not already done
        if not _telemetry_initialized:
            try:
                initialize_telemetry()
                _telemetry_initialized = True
                logger.info("OpenTelemetry initialized for Ollama client")
            except Exception as e:
                logger.warning(f"Failed to initialize telemetry: {e}")

        _ollama_client = InstrumentedOllamaClient(
            host=settings.ollama_host,
            model=settings.ollama_model,
        )
        logger.info("Created instrumented Ollama client instance")

    return _ollama_client


@lru_cache
def get_tool_registry() -> ToolRegistry:
    """Get or create the tool registry singleton.

    Returns:
        Tool registry instance
    """
    global _tool_registry

    if _tool_registry is None:
        _tool_registry = ToolRegistry()
        logger.info("Created tool registry instance")

    return _tool_registry


def get_conversation_manager(settings: Settings | None = None) -> ConversationManager:
    """Create a new conversation manager (session-scoped).

    Args:
        settings: Application settings

    Returns:
        Conversation manager instance
    """
    if settings is None:
        settings = get_settings()

    return ConversationManager(max_history=settings.max_conversation_history)


def get_chat_service() -> ChatService:
    """Get or create the chat service singleton.

    Returns:
        Chat service instance
    """
    global _chat_service

    if _chat_service is None:
        settings = get_settings()
        mcp_client = get_mcp_client(settings)
        ollama_client = get_ollama_client(settings)
        tool_registry = get_tool_registry()
        conversation_manager = get_conversation_manager(settings)

        _chat_service = ChatService(
            mcp_client=mcp_client,
            ollama_client=ollama_client,
            tool_registry=tool_registry,
            conversation_manager=conversation_manager,
        )
        logger.info("Created chat service instance")

    return _chat_service


async def initialize_services() -> None:
    """Initialize all services at application startup."""
    logger.info("Initializing application services")
    chat_service = get_chat_service()
    await chat_service.initialize()
    logger.info("Application services initialized successfully")


async def shutdown_services() -> None:
    """Shutdown all services at application shutdown."""
    logger.info("Shutting down application services")
    global _chat_service, _mcp_client, _ollama_client, _tool_registry, _telemetry_initialized

    if _chat_service:
        await _chat_service.shutdown()
        _chat_service = None

    _mcp_client = None
    _ollama_client = None
    _tool_registry = None
    _telemetry_initialized = False

    logger.info("Application services shut down successfully")
