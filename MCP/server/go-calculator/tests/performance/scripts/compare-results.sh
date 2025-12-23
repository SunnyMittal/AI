#!/bin/bash

# Performance Results Comparison Script
# Compares k6 results with Go benchmarks and generates a report

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
RESULTS_DIR="$PROJECT_ROOT/tests/performance/results"

echo "Performance Comparison Report Generator"
echo "========================================"
echo ""

# Run Go benchmarks
echo "Running Go benchmarks..."
cd "$PROJECT_ROOT"
GO_BENCH_FILE="$RESULTS_DIR/go-bench-$(date +%Y%m%d-%H%M%S).txt"
go test -bench=. -benchmem ./... > "$GO_BENCH_FILE" 2>&1 || true
echo "Go benchmarks saved to: $GO_BENCH_FILE"
echo ""

# Find most recent k6 benchmark results
K6_BENCH_FILE=$(ls -t "$RESULTS_DIR"/k6-bench*.json 2>/dev/null | head -1)

if [ -z "$K6_BENCH_FILE" ]; then
    echo "No k6 benchmark results found. Run 'make perf-benchmark' first."
    echo ""
    echo "Go benchmark results:"
    cat "$GO_BENCH_FILE" | grep "^Benchmark"
    exit 0
fi

echo "Found k6 benchmark results: $K6_BENCH_FILE"
echo ""

# Generate markdown report
REPORT_FILE="$RESULTS_DIR/comparison-$(date +%Y%m%d-%H%M%S).md"

cat > "$REPORT_FILE" << 'HEADER'
# Performance Test Results Comparison

## Summary

This report compares Go micro-benchmarks with k6 end-to-end performance tests.

## Go Benchmarks (Pure Calculation)

HEADER

# Add Go benchmark results
echo '```' >> "$REPORT_FILE"
grep "^Benchmark" "$GO_BENCH_FILE" >> "$REPORT_FILE" || echo "No benchmark results found" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

cat >> "$REPORT_FILE" << 'ANALYSIS'
## k6 Benchmarks (End-to-End)

k6 results include full HTTP request/response cycle:
- JSON-RPC 2.0 encoding/decoding
- HTTP transport
- SSE formatting
- Middleware processing
- Session management

**Expected protocol overhead**: 1-5ms (difference between k6 and Go benchmarks)

## Analysis

### Protocol Overhead

The difference between Go benchmarks (nanoseconds) and k6 benchmarks (milliseconds) represents the protocol overhead.

**Components of overhead:**
1. HTTP request/response processing
2. JSON-RPC 2.0 serialization/deserialization
3. SSE (Server-Sent Events) formatting
4. Middleware execution (logging, rate limiting, validation)
5. Session management

### Baseline Metrics

ANALYSIS

# Extract k6 metrics (simplified - would need proper JSON parsing)
echo "Latest k6 benchmark file: $(basename $K6_BENCH_FILE)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "See full k6 results in the JSON file for detailed metrics." >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

cat >> "$REPORT_FILE" << 'FOOTER'
## Recommendations

1. Monitor protocol overhead trends over time
2. If overhead exceeds 10ms, investigate:
   - Middleware performance
   - JSON serialization efficiency
   - Network latency
3. Compare results across different releases
4. Track regression in CI/CD pipeline

## Historical Trends

Store baseline results in version control to track performance across releases.

FOOTER

echo "Report generated: $REPORT_FILE"
echo ""
echo "=== Comparison Summary ==="
echo ""
echo "Go Benchmarks (pure calculation):"
grep "BenchmarkAdd\|BenchmarkSubtract\|BenchmarkMultiply\|BenchmarkDivide" "$GO_BENCH_FILE" | head -4 || echo "Run 'make bench' to generate Go benchmarks"
echo ""
echo "k6 Benchmarks: See $K6_BENCH_FILE for full results"
echo ""
echo "Full report: $REPORT_FILE"
