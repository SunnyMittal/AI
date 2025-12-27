# Performance Testing Guide for py-calculator

This document describes how to perform comprehensive performance testing for the py-calculator MCP server using k6.

## Overview

The performance testing infrastructure provides:
- **Load Testing**: Baseline performance under normal/peak load
- **Stress Testing**: Find system breaking points and maximum capacity
- **Endurance Testing**: Long-running stability and memory leak detection
- **Spike Testing**: Recovery from sudden traffic bursts
- **Benchmark Testing**: Measure individual operation performance

## Prerequisites

### Install k6

**Windows (using Chocolatey)**:
```bash
choco install k6
```

**Windows (using winget)**:
```bash
winget install k6
```

**Linux (Debian/Ubuntu)**:
```bash
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 \
  --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

**macOS (using Homebrew)**:
```bash
brew install k6
```

**Or use the automated script** (Linux/macOS):
```bash
bash tests/performance/scripts/setup-k6.sh
```

### Verify Installation

```bash
k6 version
```

## Quick Start

### 1. Start the Server

```bash
# Using uv
uv run python -m calculator.server

# Or using python directly
python -m calculator.server
```

The server will start on `http://127.0.0.1:8100` by default.

### 2. Run Performance Tests

In a separate terminal:

```bash
# Quick 30-second performance check
k6 run --duration 30s --vus 10 tests/performance/k6/scenarios/load-test.js

# Or use the quick test script
# Windows PowerShell
.\tests\performance\scripts\run-quick-test.ps1

# Linux/macOS
bash tests/performance/scripts/run-quick-test.sh

# Full load test
# Windows PowerShell
.\tests\performance\scripts\run-load-test.ps1

# Linux/macOS
bash tests/performance/scripts/run-load-test.sh

# Stress test (find breaking points)
# Windows PowerShell
.\tests\performance\scripts\run-stress-test.ps1

# Linux/macOS
bash tests/performance/scripts/run-stress-test.sh

# Endurance test (2+ hours)
# Windows PowerShell
.\tests\performance\scripts\run-endurance-test.ps1

# Linux/macOS
bash tests/performance/scripts/run-endurance-test.sh

# Benchmark individual operations
k6 run tests/performance/k6/scenarios/benchmark-tools.js --out json=tests/performance/results/k6-bench.json
```

## Test Scenarios

### Load Test

**Purpose**: Establish baseline performance under realistic load

**Duration**: ~14 minutes

**Profile**:
- Ramp up: 0 → 50 VUs (1 min)
- Sustain: 50 VUs (5 min)
- Ramp up: 50 → 100 VUs (1 min)
- Sustain: 100 VUs (5 min)
- Ramp down: 100 → 0 (1 min)

**Operations Mix**:
- 40% add operations
- 30% subtract operations
- 20% multiply operations
- 10% divide operations

**Success Criteria**:
- p95 latency < 100ms
- p99 latency < 200ms
- Average latency < 50ms
- Throughput > 1000 req/s
- Error rate < 0.1%

**Run**:
```bash
# Windows PowerShell
.\tests\performance\scripts\run-load-test.ps1

# Linux/macOS
bash tests/performance/scripts/run-load-test.sh

# Or directly with k6
k6 run tests/performance/k6/scenarios/load-test.js
```

### Stress Test

**Purpose**: Find maximum capacity and breaking points

**Duration**: ~20 minutes

**Profile**:
- Progressive ramp: 100 → 200 → 400 → 800 VUs
- Hold each level for 3 minutes
- Continue until failure or significant degradation

**Monitored Metrics**:
- Server response times under extreme load
- Memory consumption
- Error rates and failure modes
- Graceful vs catastrophic failure

**Run**:
```bash
# Windows PowerShell
.\tests\performance\scripts\run-stress-test.ps1

# Linux/macOS
bash tests/performance/scripts/run-stress-test.sh
```

### Endurance Test

**Purpose**: Long-running stability and memory leak detection

**Duration**: ~2 hours 10 minutes

**Profile**:
- Ramp up: 0 → 50 VUs (5 min)
- Sustain: 50 VUs (2 hours)
- Ramp down: 50 → 0 (5 min)

**Monitored Metrics**:
- Memory growth over time
- Session cleanup effectiveness
- Response time degradation
- Connection stability

**Run**:
```bash
# Windows PowerShell
.\tests\performance\scripts\run-endurance-test.ps1

# Linux/macOS
bash tests/performance/scripts/run-endurance-test.sh
```

### Spike Test

**Purpose**: Test recovery from sudden traffic bursts

**Duration**: ~12 minutes

**Profile**:
- Baseline: 10 VUs
- Spike: Instant jump to 200 VUs (hold 1 min)
- Drop: Back to 10 VUs
- Repeat: 5 cycles

**Run**:
```bash
k6 run tests/performance/k6/scenarios/spike-test.js
```

### Benchmark Test

**Purpose**: Measure individual operation performance

**Duration**: ~5 minutes

**Test Focus**:
- Isolated testing per operation (add, subtract, multiply, divide)
- Various number ranges (small, large, decimals, negatives)
- Protocol overhead calculation

**Run**:
```bash
k6 run tests/performance/k6/scenarios/benchmark-tools.js --out json=tests/performance/results/k6-bench.json

# Or directly
k6 run tests/performance/k6/scenarios/benchmark-tools.js
```

## Understanding Results

### Console Output

```
✓ initialize: status is 200
✓ initialize: has session header
✓ tool call: status is 200
✓ tool call: response is valid SSE

checks.........................: 100.00% ✓ 45000    ✗ 0
data_received..................: 12 MB   2.0 MB/s
data_sent......................: 8.5 MB  1.4 MB/s
http_req_blocked...............: avg=2.5ms   p(95)=5ms
http_req_connecting............: avg=1.2ms   p(95)=3ms
http_req_duration..............: avg=32ms    p(95)=78ms   p(99)=145ms
  { expected_response:true }...: avg=32ms    p(95)=78ms   p(99)=145ms
http_req_failed................: 0.00%   ✓ 0        ✗ 15000
http_req_receiving.............: avg=0.5ms   p(95)=2ms
http_req_sending...............: avg=0.3ms   p(95)=1ms
http_req_waiting...............: avg=31ms    p(95)=75ms
http_reqs......................: 15000   2500/s
iterations.....................: 5000    833.33/s
mcp_session_creation_ms........: avg=45ms    p(95)=92ms
mcp_tool_call_duration_ms......: avg=28ms    p(95)=65ms
operation_add_ms...............: avg=25ms    p(95)=60ms
operation_divide_ms............: avg=31ms    p(95)=72ms
operation_multiply_ms..........: avg=27ms    p(95)=63ms
operation_subtract_ms..........: avg=26ms    p(95)=61ms
vus............................: 100     min=0   max=100
vus_max........................: 100     min=100 max=100
```

### Key Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| `http_req_duration` | Total request time | p95 < 100ms |
| `http_req_failed` | Failed requests rate | < 0.1% |
| `http_reqs` | Requests per second | > 1000/s |
| `mcp_session_creation_ms` | Session init time | p95 < 100ms |
| `mcp_tool_call_duration_ms` | Tool call latency | p95 < 50ms |
| `operation_*_ms` | Per-operation latency | p95 < 50ms |

### Threshold Failures

If a test fails thresholds, you'll see:

```
✗ http_req_duration..............: p(95)=125ms (expected < 100ms)
✗ http_reqs......................: rate=875/s (expected > 1000/s)
```

This indicates performance regression that needs investigation.

## Architecture

### Directory Structure

```
tests/performance/
├── k6/
│   ├── scenarios/          # Test scenarios
│   │   ├── load-test.js
│   │   ├── stress-test.js
│   │   ├── endurance-test.js
│   │   ├── spike-test.js
│   │   └── benchmark-tools.js
│   ├── lib/               # Shared libraries
│   │   ├── mcp-client.js  # MCP protocol client
│   │   ├── test-data.js   # Test data generators
│   │   └── thresholds.js  # Performance SLIs/SLOs
├── scripts/               # Execution scripts
│   ├── setup-k6.sh
│   ├── run-load-test.ps1
│   ├── run-load-test.sh
│   ├── run-stress-test.ps1
│   ├── run-stress-test.sh
│   ├── run-endurance-test.ps1
│   ├── run-endurance-test.sh
│   ├── run-quick-test.ps1
│   └── run-quick-test.sh
└── results/               # Historical results
    └── .gitkeep
```

### MCP Client Library

The `mcp-client.js` library provides k6-compatible functions for testing the MCP protocol:

**Functions**:
- `initializeSession()` - Create new MCP session
- `callTool(sessionId, toolName, args)` - Execute calculator operation
- `listTools(sessionId)` - List available tools
- `deleteSession(sessionId)` - Clean up session
- `parseSSEResponse(body)` - Parse SSE format
- `performCalculation(toolName, a, b)` - Convenience function for simple tests

**Example Usage**:
```javascript
import { initializeSession, callTool, deleteSession } from './lib/mcp-client.js';

export default function() {
  // Initialize session
  const sessionId = initializeSession();

  // Perform calculations
  let result = callTool(sessionId, 'add', { a: 5, b: 3 });
  console.log(`5 + 3 = ${result.result}`);  // Output: 8

  result = callTool(sessionId, 'multiply', { a: 7, b: 6 });
  console.log(`7 * 6 = ${result.result}`);  // Output: 42

  // Clean up
  deleteSession(sessionId);
}
```

## Advanced Usage

### Custom Server URL

```bash
# Windows PowerShell
$env:SERVER_URL = "http://192.168.1.100:8100"
.\tests\performance\scripts\run-load-test.ps1

# Linux/macOS
SERVER_URL=http://192.168.1.100:8100 bash tests/performance/scripts/run-load-test.sh
```

### Custom Test Duration (Quick Test)

```bash
# Windows PowerShell
$env:TEST_DURATION = "5m"
$env:TEST_VUS = "50"
.\tests\performance\scripts\run-quick-test.ps1

# Linux/macOS
TEST_DURATION=5m TEST_VUS=50 bash tests/performance/scripts/run-quick-test.sh
```

### Generate JSON Output

```bash
k6 run --out json=results.json tests/performance/k6/scenarios/load-test.js
```

## Troubleshooting

### Server Not Responding

```bash
# Check if server is running
curl http://127.0.0.1:8100/health

# Start the server
uv run python -m calculator.server

# Check port usage
# Windows PowerShell
Get-NetTCPConnection -LocalPort 8100

# Linux/macOS
lsof -i :8100
```

### High Error Rates

1. **Connection Issues**: Check server logs for errors
2. **Timeouts**: Increase timeout in `mcp-client.js` if needed
3. **Session Issues**: Verify session management in server

### Memory Issues

```bash
# Monitor server memory during test
# Windows PowerShell
while ($true) { Get-Process python | Select-Object PM, WS; Start-Sleep 5 }

# Linux/macOS
watch -n 5 'ps aux | grep python'
```

### k6 Installation Issues

**Windows**: Use chocolatey or winget as administrator
**Linux**: Ensure GPG keys are imported correctly
**macOS**: Update Homebrew first (`brew update`)

## Best Practices

1. **Baseline First**: Always run load test before stress test
2. **Monitor Server**: Watch CPU, memory, connections during tests
3. **Incremental Load**: Don't jump from 0 to 1000 VUs instantly
4. **Cleanup Sessions**: Always call `deleteSession()` in teardown
5. **Version Control**: Store baseline results for comparison
6. **Document Changes**: Record performance impact of code changes

## Performance Targets

| Test Type | Metric | Target | Stretch Goal |
|-----------|--------|--------|--------------|
| **Load** | p95 latency | < 100ms | < 75ms |
| **Load** | Throughput | > 1000 req/s | > 2000 req/s |
| **Load** | Error rate | < 0.1% | < 0.05% |
| **Stress** | Max VUs | > 300 | > 500 |
| **Endurance** | Memory growth | < 1MB/hour | < 100KB/hour |
| **Endurance** | Uptime | 99.9% | 99.99% |

## References

- [k6 Documentation](https://k6.io/docs/)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Performance Testing Best Practices](https://k6.io/docs/testing-guides/automated-performance-testing/)

## Support

For issues or questions:
- Check server logs: `uv run python -m calculator.server`
- Examine k6 output for detailed error messages
- Review the MCP client library code in `tests/performance/k6/lib/mcp-client.js`
