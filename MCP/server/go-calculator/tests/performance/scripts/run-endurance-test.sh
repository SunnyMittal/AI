#!/bin/bash

# Endurance Test Runner Script
# Starts the server, runs the endurance test for 2+ hours, and cleans up

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

echo "Endurance Test Runner"
echo "====================="
echo "Long-running stability test (2+ hours)"
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
    if curl -s -f http://localhost:8200/health > /dev/null 2>&1; then
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
echo "Running endurance test..."
echo -e "${YELLOW}WARNING: This test will run for over 2 hours!${NC}"
echo "Test profile:"
echo "  - Ramp up: 0 → 50 VUs (5 min)"
echo "  - Sustain: 50 VUs (2 hours)"
echo "  - Ramp down: 50 → 0 (5 min)"
echo ""
echo "Results will be saved to: $RESULTS_DIR/endurance-$TIMESTAMP.json"
echo ""
echo "Press Ctrl+C to cancel (you have 10 seconds)..."
sleep 10

# Create results directory
mkdir -p "$RESULTS_DIR"

# Run k6 test
if k6 run \
    --out "json=$RESULTS_DIR/endurance-$TIMESTAMP.json" \
    "$PROJECT_ROOT/tests/performance/k6/scenarios/endurance-test.js"; then
    echo ""
    echo -e "${GREEN}✓ Endurance test completed successfully${NC}"
    echo ""
    echo "Results saved to: $RESULTS_DIR/endurance-$TIMESTAMP.json"
    echo "Review memory trends to detect leaks"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Endurance test failed${NC}"
    exit 1
fi
