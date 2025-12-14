"""MCP server implementation for the calculator."""
from pathlib import Path
from typing import Dict, Any

from mcp.server.fastmcp import FastMCP

from calculator.calculator import Calculator

# Read sample text file
RESOURCES_DIR = Path(__file__).parent.parent / "resources"
with open(RESOURCES_DIR / "sample.txt", "r") as f:
    sample_text = f.read()

# Create FastMCP instance
mcp = FastMCP(
    "Calculator",
    instructions="A calculator that performs basic arithmetic operations."
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
    if a is None or b is None:
        return {"error": "Both numbers are required for addition"}
    result = calculator.calculate("add", a, b)
    return {"result": result}

@mcp.tool()
def subtract(a: float | None = None, b: float | None = None) -> Dict[str, Any]:
    """Subtract second number from first number."""
    if a is None or b is None:
        return {"error": "Both numbers are required for subtraction"}
    result = calculator.calculate("subtract", a, b)
    return {"result": result}

@mcp.tool()
def multiply(a: float | None = None, b: float | None = None) -> Dict[str, Any]:
    """Multiply two numbers."""
    if a is None or b is None:
        return {"error": "Both numbers are required for multiplication"}
    result = calculator.calculate("multiply", a, b)
    return {"result": result}

@mcp.tool()
def divide(a: float | None = None, b: float | None = None) -> Dict[str, Any]:
    """Divide first number by second number."""
    if a is None or b is None:
        return {"error": "Both numbers are required for division"}
    try:
        result = calculator.calculate("divide", a, b)
        return {"result": result}
    except ValueError as e:
        return {"error": str(e)}

@mcp.resource("file:///resources/sample.txt")
def sample_calculations() -> str:
    """Return the sample calculations text."""
    return sample_text

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
