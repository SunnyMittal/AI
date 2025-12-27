# Performance Tests for py-calculator MCP Server

## About py-calculator

py-calculator is a Model Context Protocol (MCP) server that provides basic arithmetic operations (addition, subtraction, multiplication, and division) through a standardized interface. Built with Python and FastMCP, it uses streamable HTTP transport for efficient communication.

The server follows SOLID principles and is designed for production use with proper input validation, error handling, and performance optimization.

## Performance Testing Overview

This directory contains a comprehensive performance testing suite built with [k6](https://k6.io/), a modern load testing tool. The tests validate that the py-calculator MCP server meets performance requirements under various load conditions.

### Why Performance Testing?

Performance testing ensures:
- **Reliability**: The server handles expected load without degradation
- **Scalability**: Understanding capacity limits and breaking points
- **Stability**: No memory leaks or resource exhaustion over time
- **Quality**: Consistent response times for all operations

## Quick Start

### Prerequisites

1. **Install k6** (load testing tool):
   ```bash
   # Windows (using Chocolatey)
   choco install k6

   # Windows (using winget)
   winget install k6

   # macOS (using Homebrew)
   brew install k6

   # Linux (using setup script)
   bash tests/performance/scripts/setup-k6.sh
   ```

2. **Start the py-calculator server**:
   ```bash
   uv run python -m calculator.server
   ```

### Run Your First Test

```bash
# Quick 30-second smoke test (recommended for first run)
# Windows PowerShell
.\tests\performance\scripts\run-quick-test.ps1

# Linux/macOS
bash tests/performance/scripts/run-quick-test.sh
```

## Available Test Scenarios

| Test | Duration | Purpose | When to Use | Script |
|------|----------|---------|-------------|--------|
| **Quick Test** | 30s | Fast smoke test | CI/CD, quick validation | `run-quick-test.*` |
| **Load Test** | ~14m | Baseline performance | Regular performance checks | `run-load-test.*` |
| **Stress Test** | ~20m | Find breaking points | Capacity planning | `run-stress-test.*` |
| **Endurance Test** | ~2h 10m | Memory leak detection | Stability validation | `run-endurance-test.*` |
| **Spike Test** | ~12m | Traffic burst recovery | Resilience testing | `tests/performance/k6/scenarios/spike-test.js` |
| **Benchmark Test** | ~5m | Individual operations | Operation optimization | `tests/performance/k6/scenarios/benchmark-tools.js` |

## Test Details

### Load Test
Tests normal and peak load conditions with realistic operation mix:
- 40% addition, 30% subtraction, 20% multiplication, 10% division
- Ramps from 0 → 50 → 100 virtual users
- **Success Criteria**: p95 < 100ms, throughput > 1000 req/s, error rate < 0.1%

### Stress Test
Progressively increases load to find system limits:
- Ramps from 100 → 200 → 400 → 800 virtual users
- Identifies graceful degradation vs catastrophic failure
- **Goal**: Determine maximum capacity

### Endurance Test
Long-running test to detect memory leaks:
- Constant 50 virtual users for 2 hours
- Monitors memory growth and response time degradation
- **Success Criteria**: Memory growth < 1MB/hour

### Spike Test
Sudden traffic bursts to test recovery:
- Alternates between 10 and 200 virtual users
- 5 spike cycles to measure consistency
- **Goal**: Verify graceful handling of sudden load changes

### Benchmark Test
Isolated performance testing per operation:
- Tests add, subtract, multiply, divide separately
- Various number ranges (small, large, decimal, negative)
- **Goal**: Identify protocol overhead and optimize operations

## Directory Structure

```
tests/performance/
├── k6/
│   ├── scenarios/          # Test scenarios
│   │   ├── load-test.js           # Baseline performance test
│   │   ├── stress-test.js         # Find breaking points
│   │   ├── endurance-test.js      # Long-running stability
│   │   ├── spike-test.js          # Traffic burst handling
│   │   └── benchmark-tools.js     # Individual operations
│   ├── lib/               # Shared libraries
│   │   ├── mcp-client.js          # MCP protocol client for k6
│   │   ├── test-data.js           # Random data generators
│   │   └── thresholds.js          # Performance SLIs/SLOs
│   └── config/            # Test configurations
├── scripts/               # Execution scripts
│   ├── setup-k6.sh               # k6 installation (Linux/macOS)
│   ├── run-quick-test.ps1        # Quick test (Windows)
│   ├── run-quick-test.sh         # Quick test (Linux/macOS)
│   ├── run-load-test.ps1         # Load test (Windows)
│   ├── run-load-test.sh          # Load test (Linux/macOS)
│   ├── run-stress-test.ps1       # Stress test (Windows)
│   ├── run-stress-test.sh        # Stress test (Linux/macOS)
│   ├── run-endurance-test.ps1    # Endurance test (Windows)
│   └── run-endurance-test.sh     # Endurance test (Linux/macOS)
└── results/               # Test results (gitignored)
    ├── .gitignore
    └── .gitkeep
```

## Performance Targets

| Metric | Target | Stretch Goal |
|--------|--------|--------------|
| **p95 Latency** | < 100ms | < 75ms |
| **p99 Latency** | < 200ms | < 150ms |
| **Throughput** | > 1000 req/s | > 2000 req/s |
| **Error Rate** | < 0.1% | < 0.05% |
| **Uptime** | 99.9% | 99.99% |
| **Memory Growth** | < 1MB/hour | < 100KB/hour |

## Usage Examples

### Run with Custom Server URL

```bash
# Windows PowerShell
$env:SERVER_URL = "http://192.168.1.100:8100"
.\tests\performance\scripts\run-load-test.ps1

# Linux/macOS
SERVER_URL=http://192.168.1.100:8100 bash tests/performance/scripts/run-load-test.sh
```

### Run with Custom Duration and Load

```bash
# Windows PowerShell
$env:TEST_DURATION = "5m"
$env:TEST_VUS = "50"
.\tests\performance\scripts\run-quick-test.ps1

# Linux/macOS
TEST_DURATION=5m TEST_VUS=50 bash tests/performance/scripts/run-quick-test.sh
```

### Direct k6 Execution

```bash
# Run specific scenario
k6 run tests/performance/k6/scenarios/load-test.js

# Save results to JSON
k6 run --out json=tests/performance/results/my-test.json tests/performance/k6/scenarios/load-test.js

# Custom parameters
k6 run --duration 2m --vus 25 tests/performance/k6/scenarios/benchmark-tools.js
```

## Understanding Results

### Key Metrics Explained

- **http_req_duration**: Total request time (includes network + processing)
- **http_req_failed**: Percentage of failed HTTP requests
- **http_reqs**: Requests per second (throughput)
- **mcp_session_creation_ms**: Time to initialize MCP session
- **mcp_tool_call_duration_ms**: Time to execute calculator operation
- **operation_*_ms**: Per-operation latency (add, subtract, multiply, divide)

### Example Output

```
✓ initialize: status is 200
✓ tool call: status is 200

http_req_duration..............: avg=32ms    p(95)=78ms   p(99)=145ms
http_reqs......................: 15000   2500/s
mcp_tool_call_duration_ms......: avg=28ms    p(95)=65ms
operation_add_ms...............: avg=25ms    p(95)=60ms
```

### Threshold Failures

When thresholds fail, you'll see:
```
✗ http_req_duration: p(95)=125ms (expected < 100ms)
```

This indicates performance regression requiring investigation.

## Troubleshooting

### Server Not Responding

```bash
# Check server health
curl http://127.0.0.1:8100/health

# Start the server
uv run python -m calculator.server

# Check if port is in use
# Windows
Get-NetTCPConnection -LocalPort 8100

# Linux/macOS
lsof -i :8100
```

### High Error Rates

1. Check server logs for exceptions
2. Verify session management is working
3. Ensure server has sufficient resources
4. Check network connectivity

### k6 Not Found

```bash
# Verify installation
k6 version

# Install if missing
# Windows: choco install k6
# macOS: brew install k6
# Linux: bash tests/performance/scripts/setup-k6.sh
```

## Best Practices

1. **Always run baseline first**: Start with load test before stress testing
2. **Monitor server resources**: Watch CPU, memory, and connections during tests
3. **Use incremental load**: Don't jump from 0 to max load instantly
4. **Version control results**: Keep historical data for trend analysis
5. **Document changes**: Note performance impact of code modifications
6. **Run regularly**: Include performance tests in CI/CD pipeline

## CI/CD Integration

For automated testing in pipelines, use the quick test:

```yaml
# Example GitHub Actions workflow
- name: Performance Test
  run: |
    uv run python -m calculator.server &
    sleep 5
    TEST_DURATION=30s TEST_VUS=10 bash tests/performance/scripts/run-quick-test.sh
```

## Additional Resources

- **Full Documentation**: [docs/performance-test.md](../../docs/performance-test.md)
- **k6 Documentation**: https://k6.io/docs/
- **MCP Specification**: https://spec.modelcontextprotocol.io/
- **FastMCP Documentation**: https://github.com/jlowin/fastmcp

## Support

For issues, questions, or contributions:
1. Review the [full documentation](../../docs/performance-test.md)
2. Check server logs: `uv run python -m calculator.server`
3. Examine k6 output for detailed error messages
4. Review MCP client implementation: `tests/performance/k6/lib/mcp-client.js`

---

**Note**: Performance results may vary based on hardware, network conditions, and system load. Establish baselines in your environment for accurate comparisons.
