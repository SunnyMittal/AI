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

### Unit Tests

Clear tests cached results

```powershell
pytest --cache-clear
```

Recursive delete all files and folder below a directory

```powershell
rmdir -r .\.pytest_cache\
```

Run tests using pytest:

```bash
pytest
```

### Performance Tests

Comprehensive performance testing suite using k6 to validate server performance under various load conditions.

**Quick Start**:

1. Install k6:
   ```bash
   # Windows
   choco install k6
   # or
   winget install k6

   # macOS
   brew install k6

   # Linux
   bash tests/performance/scripts/setup-k6.sh
   ```

2. Start the server:
   ```bash
   uv run python -m calculator.server
   ```

3. Run performance tests:
   ```bash
   # Windows PowerShell
   .\tests\performance\scripts\run-quick-test.ps1

   # Linux/macOS
   bash tests/performance/scripts/run-quick-test.sh
   ```

**Available Tests**:
- **Quick Test** (30s): Fast smoke test for CI/CD
- **Load Test** (~14m): Baseline performance validation
- **Stress Test** (~20m): Find system breaking points
- **Endurance Test** (~2h): Memory leak detection
- **Spike Test** (~12m): Traffic burst recovery
- **Benchmark Test** (~5m): Individual operation performance

**Performance Targets**:
- p95 Latency: < 100ms
- Throughput: > 1000 req/s
- Error Rate: < 0.1%

For detailed documentation, see:
- [Performance Testing Guide](docs/performance-test.md)
- [Performance Tests README](tests/performance/README.md)

## License

MIT