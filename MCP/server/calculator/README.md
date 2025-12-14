# Calculator MCP Server

A Model Context Protocol (MCP) server implementing basic calculator operations using Python and uv package manager.

## Features

- Basic arithmetic operations (add, subtract, multiply, divide)
- Input validation and parameter checking
- SOLID principles implementation
- Sample text resource integration
- Performance optimized

## Installation

1. Make sure you have Python 3.8+ and uv package manager installed
2. Clone this repository
3. Create and activate a virtual environment:
   ```bash
   uv venv
   .venv/Scripts/activate
   ```
4. Install dependencies:
   ```bash
   uv pip install -e .
   ```

## Usage

Run the MCP server:

```bash
python -m calculator.server
```

While using uv package manager use below command
```
uv run python calculator/server.py
```

**Note: Run as module instead**
```
uv run python -m calculator.server
```

## Development

The project follows SOLID principles:
- Single Responsibility: Each class has one responsibility
- Open/Closed: New operations can be added without modifying existing code
- Liskov Substitution: Operations follow a common interface
- Interface Segregation: Clean separation of concerns
- Dependency Inversion: High-level modules depend on abstractions

## Testing

Run tests using pytest:

```bash
pytest
```

## License

MIT