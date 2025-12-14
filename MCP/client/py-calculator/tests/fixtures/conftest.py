"""Pytest fixtures for testing."""

import pytest

from app.domain.models import Message, MessageRole
from app.infrastructure.tool_registry import ToolRegistry
from app.services.conversation_manager import ConversationManager


@pytest.fixture
def sample_tool():
    """Sample tool definition."""
    return {
        "name": "add",
        "description": "Add two numbers",
        "inputSchema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
            },
            "required": ["a", "b"],
        },
    }


@pytest.fixture
def tool_registry():
    """Create a fresh tool registry for testing."""
    return ToolRegistry()


@pytest.fixture
def conversation_manager():
    """Create a conversation manager for testing."""
    return ConversationManager(max_history=10)


@pytest.fixture
def sample_message():
    """Sample message."""
    return Message(role=MessageRole.USER, content="Hello, world!")
