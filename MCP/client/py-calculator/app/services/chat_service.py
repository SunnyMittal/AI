"""Chat service for orchestrating LLM and MCP tool interactions."""

import json
import logging
from typing import AsyncIterator

from app.domain.exceptions import ToolExecutionError
from app.domain.models import Message, MessageRole
from app.infrastructure.mcp_client import MCPClientAdapter
from app.infrastructure.ollama_client import OllamaAdapter
from app.infrastructure.tool_registry import ToolRegistry
from app.services.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)


class ChatService:
    """Orchestrates chat interactions between user, LLM, and MCP tools."""

    def __init__(
        self,
        mcp_client: MCPClientAdapter,
        ollama_client: OllamaAdapter,
        tool_registry: ToolRegistry,
        conversation_manager: ConversationManager,
    ) -> None:
        """Initialize the chat service.

        Args:
            mcp_client: MCP client for tool execution
            ollama_client: Ollama client for LLM interactions
            tool_registry: Registry of available tools
            conversation_manager: Manager for conversation history
        """
        self._mcp = mcp_client
        self._ollama = ollama_client
        self._tools = tool_registry
        self._conversation = conversation_manager

    async def initialize(self) -> None:
        """Initialize the chat service by connecting to MCP and discovering tools."""
        logger.info("Initializing chat service")

        await self._mcp.connect()

        tools = await self._mcp.list_tools()
        self._tools.register_tools(tools)
        logger.info(f"Registered {len(self._tools)} tools")

        await self._ollama.verify_connection()
        logger.info("Chat service initialized successfully")

    async def shutdown(self) -> None:
        """Shutdown the chat service and cleanup resources."""
        logger.info("Shutting down chat service")
        await self._mcp.disconnect()

    async def process_message(self, user_input: str) -> AsyncIterator[str]:
        """Process a user message and stream the response.

        Args:
            user_input: User's message

        Yields:
            Response chunks as they are generated
        """
        logger.info(f"Processing user message: {user_input}")

        user_message = Message(role=MessageRole.USER, content=user_input)
        self._conversation.add_message(user_message)

        messages = self._conversation.to_ollama_format()
        tools = self._tools.to_ollama_format()

        try:
            response = await self._ollama.chat_with_tools(messages, tools)

            if not response or "message" not in response:
                yield "Error: Invalid response from LLM"
                return

            response_message = response["message"]

            if "tool_calls" in response_message and response_message["tool_calls"]:
                async for chunk in self._handle_tool_calls(response_message["tool_calls"]):
                    yield chunk
            else:
                content = response_message.get("content", "")
                if content:
                    assistant_message = Message(role=MessageRole.ASSISTANT, content=content)
                    self._conversation.add_message(assistant_message)
                    yield content
                else:
                    yield "I'm not sure how to respond to that."

        except Exception as e:
            error_msg = f"Error processing message: {e}"
            logger.error(error_msg)
            yield error_msg

    async def _handle_tool_calls(self, tool_calls: list[dict]) -> AsyncIterator[str]:
        """Handle tool calls from the LLM.

        Args:
            tool_calls: List of tool calls from LLM

        Yields:
            Response chunks after tool execution
        """
        logger.info(f"Handling {len(tool_calls)} tool call(s)")

        for tool_call in tool_calls:
            function = tool_call.get("function", {})
            tool_name = function.get("name", "")
            arguments = function.get("arguments", {})

            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    yield f"Error: Invalid tool arguments format"
                    return

            # Coerce numeric string arguments to actual numbers for calculator tools
            coerced_arguments = self._coerce_numeric_arguments(arguments)
            logger.info(f"Executing tool: {tool_name} with arguments: {coerced_arguments}")

            try:
                result = await self._mcp.call_tool(tool_name, coerced_arguments)

                if "error" in result:
                    error_msg = result["error"]
                    logger.error(f"Tool execution error: {error_msg}")
                    yield f"Error executing {tool_name}: {error_msg}"
                    return

                tool_result_content = json.dumps(result)
                logger.info(f"Tool result: {tool_result_content}")

                messages = self._conversation.to_ollama_format()
                messages.append({
                    "role": "assistant",
                    "content": "",
                    "tool_calls": tool_calls,
                })
                messages.append({
                    "role": "tool",
                    "content": tool_result_content,
                })

                tools = self._tools.to_ollama_format()
                final_response = await self._ollama.chat_with_tools(messages, tools)

                if "message" in final_response:
                    content = final_response["message"].get("content", "")
                    if content:
                        assistant_message = Message(
                            role=MessageRole.ASSISTANT, content=content
                        )
                        self._conversation.add_message(assistant_message)
                        yield content
                    else:
                        yield "Operation completed successfully."
                else:
                    yield "Operation completed successfully."

            except ToolExecutionError as e:
                error_msg = f"Failed to execute tool: {e}"
                logger.error(error_msg)
                yield error_msg
            except Exception as e:
                error_msg = f"Unexpected error during tool execution: {e}"
                logger.error(error_msg)
                yield error_msg

    def _coerce_numeric_arguments(self, arguments: dict) -> dict:
        """Coerce string numeric arguments to actual numbers.

        LLMs sometimes return numbers as strings, which can cause
        validation errors on the MCP server side.

        Args:
            arguments: Tool arguments dictionary

        Returns:
            Arguments with numeric strings converted to numbers
        """
        coerced = {}
        for key, value in arguments.items():
            if isinstance(value, str):
                # Try to convert to int first, then float
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

    def clear_conversation(self) -> None:
        """Clear the conversation history."""
        self._conversation.clear()
        logger.info("Conversation cleared")

    def get_conversation_history(self) -> list[Message]:
        """Get the current conversation history.

        Returns:
            List of messages in the conversation
        """
        return self._conversation.get_history()
