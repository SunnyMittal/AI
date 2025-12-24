# Prompts
Create an MCP server that exposes tools to perform addition, subtaction, multiplication and division operations.
Uses streamable HTTP transport.

## Run calculator MCP server
uv run python -m calculator.server

## Configuration
- **Transport**: Streamable HTTP
- **Default URL**: http://127.0.0.1:8000/mcp
- **Host**: 127.0.0.1 (configurable via FASTMCP_HOST env var)
- **Port**: 8000 (configurable via FASTMCP_PORT env var)
- **Path**: /mcp (configurable via FASTMCP_STREAMABLE_HTTP_PATH env var)

generate a prompt to be able to generate such a MCP servers again deterministically and accurately
    write the document to /docs/regen.md file

<!-- performance test implementation prompt -->
refer to below documents and implement performance tests for py-calculator
    D:\AI\MCP\server\go-calculator\docs\performance-test.md

<!-- observability and monitoring prompt -->
refer to below document and implement observability and monitoring for py-calculator to send the telemetry information to local instance of phoenix hosted at http://localhost:6006/
    D:\AI\MCP\server\go-calculator\docs\obs-mon.md