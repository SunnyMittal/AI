#!/bin/bash

# Backend Gateway Verification Script
# This script verifies that Kong Gateway and all backend services are properly configured

echo "=========================================="
echo "Backend Gateway Setup Verification"
echo "=========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a service is running
check_service() {
    local name=$1
    local url=$2
    local expected=$3

    echo -n "Checking $name... "

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)

    if [ "$response" = "$expected" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Expected HTTP $expected, got $response)"
        return 1
    fi
}

# Function to check if a service is reachable
check_reachable() {
    local name=$1
    local url=$2

    echo -n "Checking $name... "

    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

echo "1. Checking Backend Services (Direct Access)"
echo "--------------------------------------------"
check_service "Python Calculator (py-calculator)" "http://localhost:8100/health" "200"
check_service "Go Calculator (go-calculator)" "http://localhost:8200/" "404"  # 404 is expected for root
check_reachable "Arize Phoenix" "http://localhost:6006/"
check_service "Ollama LLM" "http://localhost:11434/api/version" "200"
echo ""

echo "2. Checking Kong Gateway"
echo "--------------------------------------------"
check_service "Kong Admin API" "http://localhost:8001/status" "200"
check_reachable "Kong Admin GUI" "http://localhost:8002/"
# Note: Prometheus metrics require KONG_STATUS_LISTEN in docker-compose.yml to match port 9080
# If this fails, verify docker-compose.yml has: KONG_STATUS_LISTEN: '0.0.0.0:9080'
check_service "Kong Status (Prometheus)" "http://localhost:9080/metrics" "200"
echo ""

echo "3. Checking Kong Routes (Through Gateway)"
echo "--------------------------------------------"
check_service "py-calculator via Kong" "http://localhost:8000/py-calculator/health" "200"
check_service "go-calculator via Kong" "http://localhost:8000/go-calculator/" "404"  # 404 is expected
check_reachable "Phoenix via Kong" "http://localhost:8000/phoenix/"
check_service "Ollama via Kong" "http://localhost:8000/ollama/api/version" "200"
echo ""

echo "4. Checking Upstream Health"
echo "--------------------------------------------"

check_upstream_health() {
    local name=$1
    local upstream=$2

    echo -n "Checking $name upstream... "

    response=$(curl -s "http://localhost:8001/upstreams/$upstream/health" 2>/dev/null)

    if [ -z "$response" ]; then
        echo -e "${RED}✗ FAILED${NC} (no response)"
        return 1
    fi

    # Check if response contains error (upstream not found)
    if echo "$response" | grep -q '"message"'; then
        echo -e "${YELLOW}⚠ UPSTREAM NOT FOUND${NC}"
        return 1
    fi

    # Parse JSON to find healthy targets using jq if available, otherwise grep
    if command -v jq &> /dev/null; then
        healthy_count=$(echo "$response" | jq '[.data[] | select(.health == "HEALTHY")] | length' 2>/dev/null)
        if [ "$healthy_count" -gt 0 ] 2>/dev/null; then
            echo -e "${GREEN}✓ OK${NC} ($healthy_count healthy target(s))"
            return 0
        else
            total_count=$(echo "$response" | jq '.data | length' 2>/dev/null)
            if [ "$total_count" -gt 0 ] 2>/dev/null; then
                echo -e "${YELLOW}⚠ UNHEALTHY${NC} (targets exist but not healthy)"
            else
                echo -e "${YELLOW}⚠ NO TARGETS${NC}"
            fi
            return 1
        fi
    else
        # Fallback: simple grep for "HEALTHY" in response
        if echo "$response" | grep -q '"health":"HEALTHY"'; then
            echo -e "${GREEN}✓ OK${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ UNHEALTHY or NO TARGETS${NC}"
            return 1
        fi
    fi
}

check_upstream_health "py-calculator" "py-calculator-upstream"
check_upstream_health "go-calculator" "go-calculator-upstream"
echo ""

echo "5. Verifying Configuration Files"
echo "--------------------------------------------"
echo "Checking frontend client .env..."
if grep -q "PHOENIX_ENDPOINT=http://localhost:8000/phoenix/v1/traces" "D:/AI/MCP/client/py-calculator/.env"; then
    echo -e "${GREEN}✓ Frontend routes through Kong${NC}"
else
    echo -e "${YELLOW}⚠ Frontend may be using direct Phoenix endpoint${NC}"
fi

echo "Checking py-calculator server .env..."
if grep -q "PHOENIX_ENDPOINT=http://localhost:8000/phoenix/v1/traces" "D:/AI/MCP/server/py-calculator/.env"; then
    echo -e "${GREEN}✓ py-calculator routes through Kong${NC}"
else
    echo -e "${YELLOW}⚠ py-calculator may be using direct Phoenix endpoint${NC}"
fi

echo "Checking go-calculator server .env..."
if grep -q "PHOENIX_ENDPOINT=http://localhost:8000/phoenix/v1/traces" "D:/AI/MCP/server/go-calculator/.env"; then
    echo -e "${GREEN}✓ go-calculator routes through Kong${NC}"
else
    echo -e "${YELLOW}⚠ go-calculator may be using direct Phoenix endpoint${NC}"
fi
echo ""

echo "6. Testing Telemetry Flow"
echo "--------------------------------------------"
# Phoenix OTLP endpoint - GET returns 200 (endpoint info page), POST accepts traces
check_reachable "Phoenix OTLP endpoint via Kong" "http://localhost:8000/phoenix/v1/traces"
echo ""

echo "=========================================="
echo "Verification Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. If Kong is not running: cd D:/AI/MCP/server/backend-gateway && docker-compose up -d"
echo "2. If backend services are not running, start them individually"
echo "3. Restart any services after updating .env files"
echo "4. Test the full application flow through Kong Gateway"
echo ""
