"""Tool registry for managing and transforming MCP tool schemas."""

import logging
from typing import Any

from app.domain.exceptions import ToolNotFoundError

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for MCP tools with schema transformation capabilities."""

    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: dict[str, dict[str, Any]] = {}

    def register_tool(self, tool: dict[str, Any]) -> None:
        """Register a tool in the registry.

        Args:
            tool: Tool definition with name, description, and inputSchema
        """
        name = tool.get("name")
        if not name:
            logger.warning("Skipping tool without name")
            return

        self._tools[name] = tool
        logger.info(f"Registered tool: {name}")

    def register_tools(self, tools: list[dict[str, Any]]) -> None:
        """Register multiple tools at once.

        Args:
            tools: List of tool definitions
        """
        for tool in tools:
            self.register_tool(tool)

    def get_tool(self, name: str) -> dict[str, Any]:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool definition

        Raises:
            ToolNotFoundError: If tool is not found
        """
        tool = self._tools.get(name)
        if not tool:
            raise ToolNotFoundError(f"Tool '{name}' not found in registry")
        return tool

    def get_all_tools(self) -> list[dict[str, Any]]:
        """Get all registered tools.

        Returns:
            List of all tool definitions
        """
        return list(self._tools.values())

    def tool_exists(self, name: str) -> bool:
        """Check if a tool exists in the registry.

        Args:
            name: Tool name

        Returns:
            True if tool exists, False otherwise
        """
        return name in self._tools

    def to_ollama_format(self) -> list[dict[str, Any]]:
        """Transform MCP tool schemas to Ollama function calling format.

        Returns:
            List of tools in Ollama function format
        """
        ollama_tools = []

        for tool in self._tools.values():
            ollama_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": self._transform_input_schema(tool.get("inputSchema", {})),
                },
            }
            ollama_tools.append(ollama_tool)

        logger.debug(f"Transformed {len(ollama_tools)} tools to Ollama format")
        return ollama_tools

    def _transform_input_schema(self, input_schema: dict[str, Any]) -> dict[str, Any]:
        """Transform MCP inputSchema to Ollama parameters format.

        Args:
            input_schema: MCP tool input schema (JSON Schema format)

        Returns:
            Ollama-compatible parameters schema
        """
        if not input_schema:
            return {"type": "object", "properties": {}, "required": []}

        properties = input_schema.get("properties", {})

        enhanced_properties = {}
        for prop_name, prop_schema in properties.items():
            enhanced_prop = prop_schema.copy()

            if "description" not in enhanced_prop:
                enhanced_prop["description"] = f"The {prop_name} parameter"

            enhanced_properties[prop_name] = enhanced_prop

        return {
            "type": "object",
            "properties": enhanced_properties,
            "required": input_schema.get("required", []),
        }

    def clear(self) -> None:
        """Clear all tools from the registry."""
        self._tools.clear()
        logger.info("Cleared tool registry")

    def __len__(self) -> int:
        """Get the number of registered tools."""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools
