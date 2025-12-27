#!/bin/bash
# Run Quick Performance Test for MCP Calculator Server
# Linux/macOS Bash script
# Use this for quick smoke tests or CI/CD pipelines

set -e

echo "========================================"
echo "MCP Calculator - Quick Test"
echo "========================================"

# Configuration
SERVER_URL=${SERVER_URL:-"http://127.0.0.1:8100"}
DURATION=${TEST_DURATION:-"30s"}
VUS=${TEST_VUS:-"5"}

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

echo ""
echo "Starting quick performance test..."
echo "Duration: $DURATION"
echo "VUs: $VUS"
echo ""

# Run the test
SERVER_URL=$SERVER_URL k6 run --duration "$DURATION" --vus "$VUS" tests/performance/k6/scenarios/load-test.js

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "Quick Test PASSED"
    echo "========================================"
else
    echo ""
    echo "========================================"
    echo "Quick Test FAILED"
    echo "========================================"
    exit 1
fi
