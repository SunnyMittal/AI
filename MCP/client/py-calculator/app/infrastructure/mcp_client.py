"""MCP client adapter for connecting to the calculator server."""

import json
import logging
from typing import Any, Protocol

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.domain.exceptions import MCPConnectionError, ToolExecutionError

logger = logging.getLogger(__name__)


class MCPClientAdapter(Protocol):
    """Protocol defining the MCP client interface."""

    async def connect(self) -> None:
        """Connect to the MCP server."""
        ...

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        ...

    async def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools from the MCP server."""
        ...

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on the MCP server."""
        ...


class StdioMCPClient:
    """MCP client implementation using stdio transport."""

    def __init__(self, server_path: str, python_path: str) -> None:
        """Initialize the MCP client.

        Args:
            server_path: Path to the calculator server directory
            python_path: Path to the Python executable for the server
        """
        self.server_path = server_path
        self.python_path = python_path
        self._session: ClientSession | None = None
        self._exit_stack: Any = None
        self._tools_cache: list[dict[str, Any]] | None = None

    async def connect(self) -> None:
        """Connect to the MCP calculator server via stdio."""
        try:
            from contextlib import AsyncExitStack

            logger.info(f"Connecting to MCP server at {self.server_path}")

            server_params = StdioServerParameters(
                command=self.python_path,
                args=["-m", "calculator.server"],
                env=None,
            )

            exit_stack = AsyncExitStack()
            self._exit_stack = exit_stack

            stdio_transport = await exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self._stdio = stdio_transport
            self._session = await exit_stack.enter_async_context(
                ClientSession(stdio_transport[0], stdio_transport[1])
            )

            await self._session.initialize()
            logger.info("Successfully connected to MCP server")

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise MCPConnectionError(f"Failed to connect to MCP server: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        try:
            if self._exit_stack:
                await self._exit_stack.aclose()
                self._exit_stack = None
                self._session = None
                logger.info("Disconnected from MCP server")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    async def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools from the MCP server.

        Returns:
            List of tool definitions with name, description, and input schema

        Raises:
            MCPConnectionError: If not connected to the server
        """
        if not self._session:
            raise MCPConnectionError("Not connected to MCP server")

        if self._tools_cache is not None:
            return self._tools_cache

        try:
            response = await self._session.list_tools()
            tools = [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "inputSchema": tool.inputSchema,
                }
                for tool in response.tools
            ]
            self._tools_cache = tools
            logger.info(f"Discovered {len(tools)} tools from MCP server")
            return tools

        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            raise MCPConnectionError(f"Failed to list tools: {e}") from e

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on the MCP server.

        Args:
            name: Tool name (e.g., "add", "subtract")
            arguments: Tool arguments (e.g., {"a": 10, "b": 5})

        Returns:
            Tool result as a dictionary

        Raises:
            MCPConnectionError: If not connected to the server
            ToolExecutionError: If tool execution fails
        """
        if not self._session:
            raise MCPConnectionError("Not connected to MCP server")

        try:
            logger.info(f"Calling tool '{name}' with arguments: {arguments} (types: {[(k, type(v).__name__) for k, v in arguments.items()]})")
            response = await self._session.call_tool(name, arguments)

            if response.isError:
                error_msg = str(response.content)
                logger.error(f"Tool '{name}' returned error: {error_msg}")
                return {"error": error_msg}

            result_content = response.content
            if isinstance(result_content, list) and len(result_content) > 0:
                first_content = result_content[0]
                if hasattr(first_content, "text"):
                    import json

                    try:
                        result_dict = json.loads(first_content.text)
                        logger.debug(f"Tool '{name}' returned: {result_dict}")
                        return result_dict
                    except json.JSONDecodeError:
                        return {"result": first_content.text}

            return {"result": str(result_content)}

        except Exception as e:
            logger.error(f"Failed to execute tool '{name}': {e}")
            raise ToolExecutionError(f"Failed to execute tool '{name}': {e}") from e


class HttpMCPClient:
    """MCP client implementation using direct HTTP/JSON-RPC for FastMCP streamable-http."""

    def __init__(self, server_url: str) -> None:
        """Initialize the HTTP MCP client.

        Args:
            server_url: URL of the MCP server (e.g., http://127.0.0.1:8000/mcp)
        """
        self.server_url = server_url
        self._client: httpx.AsyncClient | None = None
        self._session_id: str | None = None
        self._tools_cache: list[dict[str, Any]] | None = None
        self._request_id = 0

    async def connect(self) -> None:
        """Connect to the MCP server via HTTP."""
        try:
            logger.info(f"Connecting to MCP server at {self.server_url}")

            self._client = httpx.AsyncClient(timeout=30.0)

            # Initialize the MCP session
            init_request = {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "py-calculator",
                        "version": "0.1.0"
                    }
                }
            }

            response = await self._client.post(
                self.server_url,
                json=init_request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            response.raise_for_status()

            # Extract session ID from headers
            self._session_id = response.headers.get("mcp-session-id")
            if not self._session_id:
                raise MCPConnectionError("Server did not return a session ID")

            # Parse SSE response
            result = self._parse_sse_response(response.text)
            if "error" in result:
                raise MCPConnectionError(f"Initialization failed: {result['error']}")

            # Send initialized notification (required by MCP protocol)
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }

            await self._client.post(
                self.server_url,
                json=initialized_notification,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": self._session_id
                }
            )

            logger.info(f"Successfully connected to MCP server (session: {self._session_id})")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error connecting to MCP server: {e}")
            raise MCPConnectionError(f"Failed to connect to MCP server: {e}") from e
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise MCPConnectionError(f"Failed to connect to MCP server: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        try:
            if self._client:
                await self._client.aclose()
                self._client = None
                self._session_id = None

            logger.info("Disconnected from MCP server")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    def _next_request_id(self) -> int:
        """Get the next request ID."""
        self._request_id += 1
        return self._request_id

    def _parse_sse_response(self, text: str) -> dict[str, Any]:
        """Parse Server-Sent Events response format.

        Args:
            text: SSE formatted response text

        Returns:
            Parsed JSON-RPC response
        """
        # SSE format: "event: message\ndata: {...}\n\n"
        lines = text.strip().split('\n')
        for line in lines:
            if line.startswith('data: '):
                data_str = line[6:]  # Remove 'data: ' prefix
                return json.loads(data_str)

        # If no data line found, try to parse the whole text as JSON
        return json.loads(text)

    async def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools from the MCP server.

        Returns:
            List of tool definitions with name, description, and input schema

        Raises:
            MCPConnectionError: If not connected to the server
        """
        if not self._client or not self._session_id:
            raise MCPConnectionError("Not connected to MCP server")

        if self._tools_cache is not None:
            return self._tools_cache

        try:
            request = {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "tools/list"
            }

            response = await self._client.post(
                self.server_url,
                json=request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": self._session_id
                }
            )
            response.raise_for_status()

            # Parse SSE response
            result = self._parse_sse_response(response.text)
            if "error" in result:
                raise MCPConnectionError(f"Failed to list tools: {result['error']}")

            tools_data = result.get("result", {}).get("tools", [])
            tools = [
                {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "inputSchema": tool.get("inputSchema", {}),
                }
                for tool in tools_data
            ]
            self._tools_cache = tools
            logger.info(f"Discovered {len(tools)} tools from MCP server")
            return tools

        except httpx.HTTPError as e:
            logger.error(f"HTTP error listing tools: {e}")
            raise MCPConnectionError(f"Failed to list tools: {e}") from e
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            raise MCPConnectionError(f"Failed to list tools: {e}") from e

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on the MCP server.

        Args:
            name: Tool name (e.g., "add", "subtract")
            arguments: Tool arguments (e.g., {"a": 10, "b": 5})

        Returns:
            Tool result as a dictionary

        Raises:
            MCPConnectionError: If not connected to the server
            ToolExecutionError: If tool execution fails
        """
        if not self._client or not self._session_id:
            raise MCPConnectionError("Not connected to MCP server")

        try:
            logger.info(f"Calling tool '{name}' with arguments: {arguments} (types: {[(k, type(v).__name__) for k, v in arguments.items()]})")

            request = {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "tools/call",
                "params": {
                    "name": name,
                    "arguments": arguments
                }
            }

            logger.debug(f"Sending tools/call request: {json.dumps(request)}")
            logger.debug(f"Session ID: {self._session_id}")

            response = await self._client.post(
                self.server_url,
                json=request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": self._session_id
                }
            )

            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code}: {response.text}")

            response.raise_for_status()

            # Parse SSE response
            result = self._parse_sse_response(response.text)
            if "error" in result:
                error_msg = result["error"].get("message", str(result["error"]))
                logger.error(f"Tool '{name}' returned error: {error_msg}")
                return {"error": error_msg}

            # Extract the result from the JSON-RPC response
            tool_result = result.get("result", {})

            # Handle content array format
            if "content" in tool_result:
                content = tool_result["content"]
                if isinstance(content, list) and len(content) > 0:
                    first_content = content[0]
                    if isinstance(first_content, dict) and "text" in first_content:
                        try:
                            result_dict = json.loads(first_content["text"])
                            logger.debug(f"Tool '{name}' returned: {result_dict}")
                            return result_dict
                        except json.JSONDecodeError:
                            return {"result": first_content["text"]}
                    return {"result": str(first_content)}
                return {"result": str(content)}

            logger.debug(f"Tool '{name}' returned: {tool_result}")
            return tool_result

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling tool '{name}': {e}")
            raise ToolExecutionError(f"Failed to execute tool '{name}': {e}") from e
        except Exception as e:
            logger.error(f"Failed to execute tool '{name}': {e}")
            raise ToolExecutionError(f"Failed to execute tool '{name}': {e}") from e
