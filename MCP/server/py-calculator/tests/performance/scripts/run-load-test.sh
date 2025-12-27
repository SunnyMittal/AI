#!/bin/bash
# Run Load Test for MCP Calculator Server
# Linux/macOS Bash script

set -e

echo "========================================"
echo "MCP Calculator - Load Test"
echo "========================================"

# Configuration
SERVER_URL=${SERVER_URL:-"http://127.0.0.1:8100"}
RESULTS_DIR="tests/performance/results"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT_FILE="$RESULTS_DIR/load-test-$TIMESTAMP.json"

# Check if k6 is installed
if ! command -v k6 &> /dev/null; then
    echo "ERROR: k6 is not installed"
    echo "Install k6 using the setup script:"
    echo "  bash tests/performance/scripts/setup-k6.sh"
    exit 1
fi

# Check if server is running
echo "Checking server availability at $SERVER_URL..."
if curl -f -s "$SERVER_URL/health" > /dev/null; then
    echo "✓ Server is running"
else
    echo "✗ Server is not responding at $SERVER_URL"
    echo "Start the server with: uv run python -m calculator.server"
    exit 1
fi

# Create results directory
mkdir -p "$RESULTS_DIR"

echo ""
echo "Starting load test..."
echo "Duration: ~14 minutes"
echo "Max VUs: 100"
echo "Results: $OUTPUT_FILE"
echo ""

# Run the test
SERVER_URL=$SERVER_URL k6 run --out "json=$OUTPUT_FILE" tests/performance/k6/scenarios/load-test.js

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "Load Test PASSED"
    echo "========================================"
else
    echo ""
    echo "========================================"
    echo "Load Test FAILED"
    echo "Check output above for details"
    echo "========================================"
    exit 1
fi
