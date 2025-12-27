#!/usr/bin/env python3
"""
Example Python client for the Go Calculator MCP Server
Requires: requests library (pip install requests)
"""

import json
import requests
from typing import Any, Dict, Optional


class MCPClient:
    """Client for interacting with MCP Calculator Server"""

    def __init__(self, base_url: str = "http://localhost:8200"):
        self.base_url = base_url
        self.messages_url = f"{base_url}/mcp/v1/messages"
        self.request_id = 0

    def _next_id(self) -> int:
        """Generate next request ID"""
        self.request_id += 1
        return self.request_id

    def _make_request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a JSON-RPC 2.0 request"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
        }

        if params:
            request["params"] = params

        try:
            response = requests.post(
                self.messages_url,
                json=request,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return {"error": str(e)}

    def check_health(self) -> Dict[str, Any]:
        """Check server health"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def get_metrics(self) -> Dict[str, Any]:
        """Get server metrics"""
        try:
            response = requests.get(f"{self.base_url}/metrics", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def initialize(
        self,
        client_name: str = "python-client",
        client_version: str = "1.0.0",
    ) -> Dict[str, Any]:
        """Initialize MCP session"""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": client_name,
                "version": client_version,
            },
        }
        return self._make_request("initialize", params)

    def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        return self._make_request("tools/list")

    def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool"""
        params = {"name": tool_name, "arguments": arguments}
        return self._make_request("tools/call", params)

    def add(self, a: float, b: float) -> Dict[str, Any]:
        """Add two numbers"""
        return self.call_tool("add", {"a": a, "b": b})

    def subtract(self, a: float, b: float) -> Dict[str, Any]:
        """Subtract b from a"""
        return self.call_tool("subtract", {"a": a, "b": b})

    def multiply(self, a: float, b: float) -> Dict[str, Any]:
        """Multiply two numbers"""
        return self.call_tool("multiply", {"a": a, "b": b})

    def divide(self, a: float, b: float) -> Dict[str, Any]:
        """Divide a by b"""
        return self.call_tool("divide", {"a": a, "b": b})


def print_response(title: str, response: Dict[str, Any]) -> None:
    """Pretty print a response"""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}")
    print(json.dumps(response, indent=2))


def extract_result(response: Dict[str, Any]) -> Optional[str]:
    """Extract the result value from a tool call response"""
    if "result" in response:
        result = response["result"]
        if "content" in result and len(result["content"]) > 0:
            return result["content"][0].get("text")
    return None


def main():
    """Run example requests"""
    print("Go Calculator MCP Server - Python Client Example")
    print("=" * 60)

    # Create client
    client = MCPClient()

    # 1. Check health
    health = client.check_health()
    print_response("1. Server Health", health)

    # 2. Initialize
    init_response = client.initialize()
    print_response("2. Initialize MCP Session", init_response)

    # 3. List tools
    tools = client.list_tools()
    print_response("3. List Available Tools", tools)

    # 4. Test add
    add_result = client.add(5, 3)
    print_response("4. Add (5 + 3)", add_result)
    result = extract_result(add_result)
    if result:
        print(f"   Result: {result}")

    # 5. Test subtract
    sub_result = client.subtract(10, 4)
    print_response("5. Subtract (10 - 4)", sub_result)
    result = extract_result(sub_result)
    if result:
        print(f"   Result: {result}")

    # 6. Test multiply
    mul_result = client.multiply(7, 6)
    print_response("6. Multiply (7 * 6)", mul_result)
    result = extract_result(mul_result)
    if result:
        print(f"   Result: {result}")

    # 7. Test divide
    div_result = client.divide(15, 3)
    print_response("7. Divide (15 / 3)", div_result)
    result = extract_result(div_result)
    if result:
        print(f"   Result: {result}")

    # 8. Test divide by zero (error case)
    div_zero = client.divide(10, 0)
    print_response("8. Divide by Zero (10 / 0) - Error Case", div_zero)

    # 9. Test with decimals
    decimal_result = client.multiply(3.14, 2.5)
    print_response("9. Multiply Decimals (3.14 * 2.5)", decimal_result)
    result = extract_result(decimal_result)
    if result:
        print(f"   Result: {result}")

    # 10. Check metrics
    metrics = client.get_metrics()
    print_response("10. Server Metrics", metrics)

    print(f"\n{'=' * 60}")
    print("All examples completed!")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
