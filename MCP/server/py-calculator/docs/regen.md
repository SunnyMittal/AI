# MCP Calculator Server Regeneration Prompt

Use this prompt to regenerate the py-calculator MCP server from scratch.

---

## Prompt

```
Create a Python MCP (Model Context Protocol) server for a calculator with the following specifications:

### Project Requirements

1. **Project Name:** calculator
2. **Python Version:** >= 3.13
3. **Package Manager:** uv (not pip)
4. **Build System:** hatchling

### Project Structure

Create the following directory structure:
```
py-calculator/
├── calculator/
│   ├── __init__.py
│   ├── calculator.py      # Calculator logic with SOLID principles
│   └── server.py          # MCP server entry point
├── tests/
│   ├── __init__.py
│   └── test_calculator.py # pytest unit tests
├── resources/
│   └── sample.txt         # Sample calculations resource
├── pyproject.toml
├── .gitignore
└── README.md
```

### Calculator Implementation (calculator/calculator.py)

Implement the calculator following SOLID principles:

1. **Abstract Base Class:** Create an `Operation` ABC with an abstract `execute(a, b)` method
2. **Concrete Operations:** Implement these classes extending `Operation`:
   - `Addition` - returns a + b
   - `Subtraction` - returns a - b
   - `Multiplication` - returns a * b
   - `Division` - returns a / b (handle division by zero with ValueError)

3. **Calculator Class:**
   - Use a dictionary to map operation names to Operation instances (Strategy pattern)
   - Provide a `calculate(operation: str, a: Number, b: Number)` method
   - Raise `ValueError` for unknown operations

4. **Type Hints:** Use `numbers.Number` for numeric type hints

### MCP Server Implementation (calculator/server.py)

1. **Framework:** Use FastMCP from the `mcp` package
2. **Server Name:** "Calculator"
3. **Transport:** Streamable HTTP (use `mcp.run(transport="streamable-http")`)

4. **Register 4 Tools:**
   - `add(a: float, b: float) -> str` - Add two numbers
   - `subtract(a: float, b: float) -> str` - Subtract b from a
   - `multiply(a: float, b: float) -> str` - Multiply two numbers
   - `divide(a: float, b: float) -> str` - Divide a by b

   Each tool should:
   - Validate that both parameters are provided (return error message if missing)
   - Return result as a formatted string like "X + Y = Z"
   - Handle errors gracefully (especially division by zero)

5. **Register 1 Resource:**
   - URI: `file:///resources/sample.txt`
   - Name: "sample_calculations"
   - Description: "Sample calculations showing basic arithmetic examples"
   - Load content from `resources/sample.txt` using `importlib.resources`

6. **Server Instructions:**
   "A simple calculator server that can perform basic arithmetic operations. Use the add, subtract, multiply, and divide tools to perform calculations."

### Resources (resources/sample.txt)

```
# Sample calculation examples
1 + 1 = 2
10 - 5 = 5
4 * 3 = 12
15 / 3 = 5
```

### Configuration (pyproject.toml)

```toml
[project]
requires-python = ">=3.13"
name = "calculator"
version = "0.1.0"
description = "A calculator MCP server with basic arithmetic operations"
dependencies = [
    "mcp @ git+https://github.com/modelcontextprotocol/python-sdk.git",
    "uvicorn"
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.metadata]
allow-direct-references = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### Tests (tests/test_calculator.py)

Create pytest tests covering:

1. **Basic Operations:**
   - `test_addition` - verify 2 + 3 = 5
   - `test_subtraction` - verify 5 - 3 = 2
   - `test_multiplication` - verify 4 * 3 = 12
   - `test_division` - verify 10 / 2 = 5

2. **Edge Cases:**
   - `test_division_by_zero` - verify ValueError is raised
   - `test_invalid_operation` - verify ValueError for unknown operations
   - `test_negative_numbers` - verify operations work with negatives
   - `test_float_operations` - verify floating point precision using `pytest.approx()`

### .gitignore

Include standard Python ignores:
- `__pycache__/`, `*.py[cod]`, `*.so`
- Virtual environments: `.venv/`, `venv/`, `env/`
- IDE files: `.idea/`, `.vscode/`, `*.swp`
- Test artifacts: `.pytest_cache/`, `.coverage`, `htmlcov/`
- Build artifacts: `*.egg-info/`, `dist/`, `build/`
- OS files: `.DS_Store`, `Thumbs.db`

### Environment Variables (Optional Configuration)

The server supports these environment variables:
- `FASTMCP_HOST` - Server host (default: 127.0.0.1)
- `FASTMCP_PORT` - Server port (default: 8100)
- `FASTMCP_STREAMABLE_HTTP_PATH` - HTTP path (default: /mcp)

### Running the Server

```bash
# Install dependencies
uv sync

# Run the server
uv run python -m calculator.server

# Run tests
uv run pytest
```

### Design Principles

1. Follow SOLID principles throughout
2. Use dependency injection via the Strategy pattern
3. Keep tools focused and single-purpose
4. Provide clear error messages
5. Include comprehensive input validation
6. Write testable code with high coverage
```

---

## Verification Checklist

After regeneration, verify:

- [ ] Server starts without errors: `uv run python -m calculator.server`
- [ ] Server responds at `http://127.0.0.1:8100/mcp`
- [ ] All 4 tools are registered (add, subtract, multiply, divide)
- [ ] Resource is accessible at `file:///resources/sample.txt`
- [ ] All tests pass: `uv run pytest`
- [ ] Division by zero returns appropriate error
- [ ] Missing parameters return validation errors
- [ ] SOLID principles are implemented in calculator.py

## Key Implementation Details

### FastMCP Tool Registration Pattern

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Calculator", instructions="...")

@mcp.tool()
def add(a: float, b: float) -> str:
    """Add two numbers together."""
    if a is None or b is None:
        return "Error: Both 'a' and 'b' parameters are required"
    result = calculator.calculate('add', a, b)
    return f"{a} + {b} = {result}"
```

### FastMCP Resource Registration Pattern

```python
from importlib import resources as impresources
from calculator import resources

@mcp.resource("file:///resources/sample.txt")
def sample_calculations() -> str:
    """Sample calculations showing basic arithmetic examples."""
    inp_file = impresources.files(resources) / "sample.txt"
    with inp_file.open("r") as f:
        return f.read()
```

### SOLID Calculator Pattern

```python
from abc import ABC, abstractmethod
from numbers import Number
from typing import Dict

class Operation(ABC):
    @abstractmethod
    def execute(self, a: Number, b: Number) -> Number:
        pass

class Addition(Operation):
    def execute(self, a: Number, b: Number) -> Number:
        return a + b

class Calculator:
    def __init__(self):
        self._operations: Dict[str, Operation] = {
            'add': Addition(),
            'subtract': Subtraction(),
            'multiply': Multiplication(),
            'divide': Division()
        }

    def calculate(self, operation: str, a: Number, b: Number) -> Number:
        if operation not in self._operations:
            raise ValueError(f"Unknown operation: {operation}")
        return self._operations[operation].execute(a, b)
```
