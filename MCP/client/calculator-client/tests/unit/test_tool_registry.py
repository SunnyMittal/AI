"""Unit tests for ToolRegistry."""

import pytest

from app.domain.exceptions import ToolNotFoundError
from app.infrastructure.tool_registry import ToolRegistry


def test_register_tool(tool_registry, sample_tool):
    """Test registering a tool."""
    tool_registry.register_tool(sample_tool)

    assert len(tool_registry) == 1
    assert "add" in tool_registry
    assert tool_registry.tool_exists("add")


def test_get_tool(tool_registry, sample_tool):
    """Test getting a tool by name."""
    tool_registry.register_tool(sample_tool)

    tool = tool_registry.get_tool("add")
    assert tool["name"] == "add"
    assert tool["description"] == "Add two numbers"


def test_get_tool_not_found(tool_registry):
    """Test getting a non-existent tool raises exception."""
    with pytest.raises(ToolNotFoundError):
        tool_registry.get_tool("nonexistent")


def test_get_all_tools(tool_registry, sample_tool):
    """Test getting all tools."""
    tool_registry.register_tool(sample_tool)

    all_tools = tool_registry.get_all_tools()
    assert len(all_tools) == 1
    assert all_tools[0]["name"] == "add"


def test_to_ollama_format(tool_registry, sample_tool):
    """Test transforming tools to Ollama format."""
    tool_registry.register_tool(sample_tool)

    ollama_tools = tool_registry.to_ollama_format()

    assert len(ollama_tools) == 1
    assert ollama_tools[0]["type"] == "function"
    assert ollama_tools[0]["function"]["name"] == "add"
    assert ollama_tools[0]["function"]["description"] == "Add two numbers"
    assert "parameters" in ollama_tools[0]["function"]
    assert ollama_tools[0]["function"]["parameters"]["type"] == "object"


def test_clear(tool_registry, sample_tool):
    """Test clearing the tool registry."""
    tool_registry.register_tool(sample_tool)
    assert len(tool_registry) == 1

    tool_registry.clear()
    assert len(tool_registry) == 0


def test_register_multiple_tools(tool_registry):
    """Test registering multiple tools."""
    tools = [
        {"name": "add", "description": "Add", "inputSchema": {}},
        {"name": "subtract", "description": "Subtract", "inputSchema": {}},
        {"name": "multiply", "description": "Multiply", "inputSchema": {}},
    ]

    tool_registry.register_tools(tools)

    assert len(tool_registry) == 3
    assert "add" in tool_registry
    assert "subtract" in tool_registry
    assert "multiply" in tool_registry
