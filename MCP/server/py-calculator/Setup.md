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