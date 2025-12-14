"""REST API endpoints."""

import logging
from typing import Any

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from app.api.dependencies import get_tool_registry

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def root() -> RedirectResponse:
    """Redirect root to the static frontend.

    Returns:
        Redirect response to the frontend
    """
    return RedirectResponse(url="/static/index.html")


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint.

    Returns:
        Health status information
    """
    tool_registry = get_tool_registry()

    return {
        "status": "healthy",
        "tools_count": len(tool_registry),
    }


@router.get("/tools")
async def list_tools() -> dict[str, Any]:
    """List all available MCP tools.

    Returns:
        Dictionary containing the list of tools
    """
    tool_registry = get_tool_registry()
    tools = tool_registry.get_all_tools()

    return {
        "tools": tools,
        "count": len(tools),
    }
