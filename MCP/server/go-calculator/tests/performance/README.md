# Performance Testing for go-calculator

This directory contains comprehensive performance testing infrastructure using k6.

## Quick Start

### 1. Install k6

**Windows**:
```powershell
choco install k6
# or
winget install k6
```

**macOS**:
```bash
brew install k6
```

**Linux**:
See [k6 installation docs](https://k6.io/docs/get-started/installation/)

Or use the automated script (Linux/macOS):
```bash
bash tests/performance/scripts/setup-k6.sh
```

### 2. Build the Server

**Windows**:
```powershell
go build -o bin/calculator-server.exe ./cmd/server
```

**Linux/macOS**:
```bash
go build -o bin/calculator-server ./cmd/server
```

### 3. Run Performance Tests

**Windows (PowerShell)**:
```powershell
# Quick 30-second check
k6 run --duration 30s --vus 10 tests/performance/k6/scenarios/load-test.js

# Full load test (~14 minutes)
.\tests\performance\scripts\run-load-test.ps1

# Stress test (~25 minutes)
.\tests\performance\scripts\run-stress-test.ps1

# Benchmark individual operations (~5 minutes)
k6 run tests/performance/k6/scenarios/benchmark-tools.js --out json=tests/performance/results/k6-bench.json

# Endurance test (2+ hours)
.\tests\performance\scripts\run-endurance-test.ps1

# Spike test (~12 minutes)
k6 run tests/performance/k6/scenarios/spike-test.js
```

**Linux/macOS (Bash)**:
```bash
# Quick 30-second check
k6 run --duration 30s --vus 10 tests/performance/k6/scenarios/load-test.js

# Full load test (~14 minutes)
bash tests/performance/scripts/run-load-test.sh

# Stress test (~25 minutes)
bash tests/performance/scripts/run-stress-test.sh

# Benchmark individual operations (~5 minutes)
k6 run tests/performance/k6/scenarios/benchmark-tools.js --out json=tests/performance/results/k6-bench.json

# Endurance test (2+ hours)
bash tests/performance/scripts/run-endurance-test.sh

# Spike test (~12 minutes)
k6 run tests/performance/k6/scenarios/spike-test.js
```

## Directory Structure

```
tests/performance/
├── k6/
│   ├── scenarios/          # Test scenarios
│   │   ├── load-test.js           # Baseline load testing
│   │   ├── stress-test.js         # Find breaking points
│   │   ├── endurance-test.js      # Long-running stability
│   │   ├── spike-test.js          # Sudden traffic spikes
│   │   └── benchmark-tools.js     # Individual tool benchmarks
│   ├── lib/               # Shared libraries
│   │   ├── mcp-client.js          # MCP protocol client
│   │   ├── test-data.js           # Test data generators
│   │   └── thresholds.js          # Performance SLIs/SLOs
│   ├── config/            # Test configurations (future)
│   └── reports/           # Generated reports
├── scripts/               # Execution scripts
│   ├── run-load-test.ps1          # Load test runner (Windows)
│   ├── run-load-test.sh           # Load test runner (Linux/macOS)
│   ├── run-stress-test.ps1        # Stress test runner (Windows)
│   ├── run-stress-test.sh         # Stress test runner (Linux/macOS)
│   ├── run-endurance-test.ps1     # Endurance test runner (Windows)
│   ├── run-endurance-test.sh      # Endurance test runner (Linux/macOS)
│   ├── setup-k6.sh                # k6 setup (Linux/macOS)
│   └── compare-results.sh         # Results comparison (Linux/macOS)
└── results/               # Test results (gitignored)
```

## Test Scenarios

### Load Test
- **Duration**: ~14 minutes
- **Purpose**: Baseline performance under normal/peak load
- **Profile**: 0→50→100 VUs with sustain periods
- **Success Criteria**: p95 < 100ms, throughput > 1000 req/s

### Stress Test
- **Duration**: ~25 minutes
- **Purpose**: Find system breaking points
- **Profile**: Progressive ramp to 800 VUs
- **Success Criteria**: Identify maximum capacity

### Endurance Test
- **Duration**: 2+ hours
- **Purpose**: Long-running stability, memory leak detection
- **Profile**: Sustain 50 VUs for 2 hours
- **Success Criteria**: No memory leaks, stable performance

### Spike Test
- **Duration**: ~12 minutes
- **Purpose**: Test recovery from sudden traffic bursts
- **Profile**: 5 cycles of 10→200→10 VUs
- **Success Criteria**: Quick recovery, low error rate

### Benchmark Test
- **Duration**: ~5 minutes
- **Purpose**: Optimize individual operations
- **Profile**: Isolated testing per operation
- **Success Criteria**: Compare with Go benchmarks

## Performance Targets

| Metric | Target | Stretch Goal |
|--------|--------|--------------|
| p95 latency | < 100ms | < 75ms |
| p99 latency | < 200ms | < 150ms |
| Throughput | > 1000 req/s | > 2000 req/s |
| Error rate | < 0.1% | < 0.05% |
| Max VUs (stress) | > 300 | > 500 |

## MCP Client Library

The `k6/lib/mcp-client.js` library provides k6-compatible functions for testing the MCP protocol:

```javascript
import { initializeSession, callTool, deleteSession } from './lib/mcp-client.js';

export default function() {
  const sessionId = initializeSession();
  const result = callTool(sessionId, 'add', { a: 5, b: 3 });
  console.log(`Result: ${result.value}`);
  deleteSession(sessionId);
}
```

## CI/CD Integration

Performance tests run automatically:
- **Pull Requests**: Quick 30-second check
- **Nightly**: Full test suite (load + stress + benchmark)
- **Manual**: Trigger any test on demand

See `.github/workflows/performance-tests.yml` for configuration.

## Documentation

Full documentation available at: `docs/performance-test.md`

## Results

Results are saved to `tests/performance/results/` with timestamps:
- `load-YYYYMMDD-HHMMSS.json`
- `stress-YYYYMMDD-HHMMSS.json`
- `k6-bench.json`

Generate comparison report (Linux/macOS):
```bash
bash tests/performance/scripts/compare-results.sh
```

## Troubleshooting

**Server not responding**:

Windows:
```powershell
curl.exe http://localhost:8000/health
```

Linux/macOS:
```bash
curl http://localhost:8000/health
```

**k6 not installed**:

Windows:
```powershell
choco install k6
# or
winget install k6
```

macOS:
```bash
brew install k6
```

Linux/macOS (automated):
```bash
bash tests/performance/scripts/setup-k6.sh
```

**High error rates**:
- Check server rate limiting (100 req/s)
- Verify server timeouts (30s default)
- Review session management

## Contributing

When adding new tests:
1. Create scenario in `k6/scenarios/`
2. Add scripts in `scripts/` (.ps1 for Windows, .sh for Linux/macOS)
3. Update documentation
4. Add CI/CD workflow step (if needed)
