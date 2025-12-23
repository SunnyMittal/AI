#!/bin/bash

# Stress Test Runner Script
# Starts the server, runs the stress test to find breaking points, and cleans up

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
RESULTS_DIR="$PROJECT_ROOT/tests/performance/results"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
SERVER_PID=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Stress Test Runner"
echo "=================="
echo "Finding system breaking points..."
echo ""

# Function to cleanup on exit
cleanup() {
    if [ -n "$SERVER_PID" ]; then
        echo ""
        echo "Stopping server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
        echo "Server stopped"
    fi
}

trap cleanup EXIT INT TERM

# Build server if needed
cd "$PROJECT_ROOT"
if [ ! -f "bin/calculator-server" ] && [ ! -f "bin/calculator-server.exe" ]; then
    echo "Building server..."
    make build
fi

# Start server in background
echo "Starting server..."
if [ -f "bin/calculator-server.exe" ]; then
    ./bin/calculator-server.exe &
else
    ./bin/calculator-server &
fi
SERVER_PID=$!
echo "Server started (PID: $SERVER_PID)"

# Wait for server to be ready
echo "Waiting for server to be ready..."
MAX_WAIT=30
WAIT_COUNT=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Server is ready${NC}"
        break
    fi
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
    echo -n "."
done

if [ $WAIT_COUNT -eq $MAX_WAIT ]; then
    echo -e "${RED}✗ Server failed to start within ${MAX_WAIT} seconds${NC}"
    exit 1
fi

echo ""
echo "Running stress test..."
echo "This will take approximately 25 minutes..."
echo "The test will ramp up to 800 VUs to find system limits"
echo "Results will be saved to: $RESULTS_DIR/stress-$TIMESTAMP.json"
echo ""

# Create results directory
mkdir -p "$RESULTS_DIR"

# Run k6 test
if k6 run \
    --out "json=$RESULTS_DIR/stress-$TIMESTAMP.json" \
    "$PROJECT_ROOT/tests/performance/k6/scenarios/stress-test.js"; then
    echo ""
    echo -e "${GREEN}✓ Stress test completed${NC}"
    echo ""
    echo "Results saved to: $RESULTS_DIR/stress-$TIMESTAMP.json"
    exit 0
else
    echo ""
    echo -e "${YELLOW}⚠ Stress test encountered failures (expected when finding limits)${NC}"
    echo "Results saved to: $RESULTS_DIR/stress-$TIMESTAMP.json"
    exit 0
fi
