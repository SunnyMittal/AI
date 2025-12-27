"""MCP server implementation for the calculator."""
from pathlib import Path
from typing import Dict, Any
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from calculator.calculator import Calculator
from calculator.telemetry import (
    initialize_telemetry,
    initialize_metrics,
    configure_logging,
    create_metrics
)

# Initialize telemetry
try:
    # Service name and version will be read from environment variables
    # (PHOENIX_PROJECT_NAME, OTEL_SERVICE_NAME, SERVICE_VERSION)
    initialize_telemetry()
    initialize_metrics()
    configure_logging()
    metrics_instruments = create_metrics()
    logging.info("Telemetry initialized successfully")
except Exception as e:
    logging.warning(f"Failed to initialize telemetry: {e}")
    metrics_instruments = None

# Read sample text file
RESOURCES_DIR = Path(__file__).parent.parent / "resources"
with open(RESOURCES_DIR / "sample.txt", "r") as f:
    sample_text = f.read()

# Read host and port from environment
_host = os.getenv("FASTMCP_HOST", "127.0.0.1")
_port = int(os.getenv("FASTMCP_PORT", "8100"))

# Create FastMCP instance
mcp = FastMCP(
    "Calculator",
    instructions="A calculator that performs basic arithmetic operations.",
    host=_host,
    port=_port
)

# Create calculator instance
calculator = Calculator()

# Load sample text resource
def _load_sample_text() -> str:
    """Load the sample text resource."""
    sample_path = Path(__file__).parent.parent / "resources" / "sample.txt"
    return sample_path.read_text()

sample_text = _load_sample_text()

@mcp.tool()
def add(a: float | None = None, b: float | None = None) -> Dict[str, Any]:
    """Add two numbers."""
    if metrics_instruments:
        metrics_instruments["tool_call_counter"].add(1, {"tool": "add"})

    if a is None or b is None:
        if metrics_instruments:
            metrics_instruments["tool_error_counter"].add(1, {"tool": "add", "error": "missing_args"})
        return {"error": "Both numbers are required for addition"}

    try:
        result = calculator.calculate("add", a, b)
        return {"result": result}
    except Exception as e:
        if metrics_instruments:
            metrics_instruments["tool_error_counter"].add(1, {"tool": "add", "error": type(e).__name__})
        raise

@mcp.tool()
def subtract(a: float | None = None, b: float | None = None) -> Dict[str, Any]:
    """Subtract second number from first number."""
    if metrics_instruments:
        metrics_instruments["tool_call_counter"].add(1, {"tool": "subtract"})

    if a is None or b is None:
        if metrics_instruments:
            metrics_instruments["tool_error_counter"].add(1, {"tool": "subtract", "error": "missing_args"})
        return {"error": "Both numbers are required for subtraction"}

    try:
        result = calculator.calculate("subtract", a, b)
        return {"result": result}
    except Exception as e:
        if metrics_instruments:
            metrics_instruments["tool_error_counter"].add(1, {"tool": "subtract", "error": type(e).__name__})
        raise

@mcp.tool()
def multiply(a: float | None = None, b: float | None = None) -> Dict[str, Any]:
    """Multiply two numbers."""
    if metrics_instruments:
        metrics_instruments["tool_call_counter"].add(1, {"tool": "multiply"})

    if a is None or b is None:
        if metrics_instruments:
            metrics_instruments["tool_error_counter"].add(1, {"tool": "multiply", "error": "missing_args"})
        return {"error": "Both numbers are required for multiplication"}

    try:
        result = calculator.calculate("multiply", a, b)
        return {"result": result}
    except Exception as e:
        if metrics_instruments:
            metrics_instruments["tool_error_counter"].add(1, {"tool": "multiply", "error": type(e).__name__})
        raise

@mcp.tool()
def divide(a: float | None = None, b: float | None = None) -> Dict[str, Any]:
    """Divide first number by second number."""
    if metrics_instruments:
        metrics_instruments["tool_call_counter"].add(1, {"tool": "divide"})

    if a is None or b is None:
        if metrics_instruments:
            metrics_instruments["tool_error_counter"].add(1, {"tool": "divide", "error": "missing_args"})
        return {"error": "Both numbers are required for division"}

    try:
        result = calculator.calculate("divide", a, b)
        return {"result": result}
    except ValueError as e:
        if metrics_instruments:
            metrics_instruments["tool_error_counter"].add(1, {"tool": "divide", "error": "ValueError"})
        return {"error": str(e)}

@mcp.resource("file:///resources/sample.txt")
def sample_calculations() -> str:
    """Return the sample calculations text."""
    return sample_text

# Add custom health endpoint for performance testing
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for monitoring and performance testing."""
    return JSONResponse({"status": "ok", "service": "calculator-mcp"})

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
