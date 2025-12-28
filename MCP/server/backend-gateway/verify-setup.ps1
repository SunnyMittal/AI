# Backend Gateway Verification Script for Windows (PowerShell)
# This script verifies that Kong Gateway and all backend services are properly configured

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Backend Gateway Setup Verification" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a service is running
function Test-Service {
    param (
        [string]$Name,
        [string]$Url,
        [int]$ExpectedStatus = 200
    )

    Write-Host "Checking $Name... " -NoNewline

    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
        $statusCode = $response.StatusCode
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
    }

    if ($statusCode -eq $ExpectedStatus) {
        Write-Host "✓ OK" -ForegroundColor Green -NoNewline
        Write-Host " (HTTP $statusCode)"
        return $true
    }
    else {
        Write-Host "✗ FAILED" -ForegroundColor Red -NoNewline
        Write-Host " (Expected HTTP $ExpectedStatus, got $statusCode)"
        return $false
    }
}

# Function to check if a service is reachable
function Test-Reachable {
    param (
        [string]$Name,
        [string]$Url
    )

    Write-Host "Checking $Name... " -NoNewline

    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        Write-Host "✓ OK" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "✗ FAILED" -ForegroundColor Red
        return $false
    }
}

Write-Host "1. Checking Backend Services (Direct Access)" -ForegroundColor Yellow
Write-Host "--------------------------------------------"
Test-Service -Name "Python Calculator (py-calculator)" -Url "http://localhost:8100/health" -ExpectedStatus 200
Test-Service -Name "Go Calculator (go-calculator)" -Url "http://localhost:8200/" -ExpectedStatus 404  # 404 is expected for root
Test-Reachable -Name "Arize Phoenix" -Url "http://localhost:6006/"
Test-Service -Name "Ollama LLM" -Url "http://localhost:11434/api/version" -ExpectedStatus 200
Write-Host ""

Write-Host "2. Checking Kong Gateway" -ForegroundColor Yellow
Write-Host "--------------------------------------------"
Test-Service -Name "Kong Admin API" -Url "http://localhost:8001/status" -ExpectedStatus 200
Test-Reachable -Name "Kong Admin GUI" -Url "http://localhost:8002/"
# Note: Prometheus metrics require KONG_STATUS_LISTEN in docker-compose.yml to match port 9080
# If this fails, verify docker-compose.yml has: KONG_STATUS_LISTEN: '0.0.0.0:9080'
Test-Service -Name "Kong Status (Prometheus)" -Url "http://localhost:9080/metrics" -ExpectedStatus 200
Write-Host ""

Write-Host "3. Checking Kong Routes (Through Gateway)" -ForegroundColor Yellow
Write-Host "--------------------------------------------"
Test-Service -Name "py-calculator via Kong" -Url "http://localhost:8000/py-calculator/health" -ExpectedStatus 200
Test-Service -Name "go-calculator via Kong" -Url "http://localhost:8000/go-calculator/" -ExpectedStatus 404  # 404 is expected
Test-Reachable -Name "Phoenix via Kong" -Url "http://localhost:8000/phoenix/"
Test-Service -Name "Ollama via Kong" -Url "http://localhost:8000/ollama/api/version" -ExpectedStatus 200
Write-Host ""

Write-Host "4. Checking Upstream Health" -ForegroundColor Yellow
Write-Host "--------------------------------------------"

function Test-UpstreamHealth {
    param (
        [string]$Name,
        [string]$Upstream
    )

    Write-Host "Checking $Name upstream... " -NoNewline
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8001/upstreams/$Upstream/health" -ErrorAction Stop
        # Kong returns JSON with data array containing targets with health status
        $healthyTargets = $response.data | Where-Object { $_.health -eq "HEALTHY" }
        if ($healthyTargets.Count -gt 0) {
            Write-Host "✓ OK" -ForegroundColor Green -NoNewline
            Write-Host " ($($healthyTargets.Count) healthy target(s))"
            return $true
        } else {
            # Check if upstream exists but no healthy targets
            if ($response.data.Count -gt 0) {
                Write-Host "⚠ UNHEALTHY" -ForegroundColor Yellow -NoNewline
                Write-Host " (targets exist but not healthy)"
            } else {
                Write-Host "⚠ NO TARGETS" -ForegroundColor Yellow
            }
            return $false
        }
    }
    catch {
        if ($_.Exception.Response.StatusCode -eq 404) {
            Write-Host "⚠ UPSTREAM NOT FOUND" -ForegroundColor Yellow
        } else {
            Write-Host "✗ FAILED" -ForegroundColor Red -NoNewline
            Write-Host " ($($_.Exception.Message))"
        }
        return $false
    }
}

Test-UpstreamHealth -Name "py-calculator" -Upstream "py-calculator-upstream"
Test-UpstreamHealth -Name "go-calculator" -Upstream "go-calculator-upstream"
Write-Host ""

Write-Host "5. Verifying Configuration Files" -ForegroundColor Yellow
Write-Host "--------------------------------------------"
Write-Host "Checking frontend client .env... " -NoNewline
if (Select-String -Path "D:\AI\MCP\client\py-calculator\.env" -Pattern "PHOENIX_ENDPOINT=http://localhost:8000/phoenix/v1/traces" -Quiet) {
    Write-Host "✓ Frontend routes through Kong" -ForegroundColor Green
} else {
    Write-Host "⚠ Frontend may be using direct Phoenix endpoint" -ForegroundColor Yellow
}

Write-Host "Checking py-calculator server .env... " -NoNewline
if (Select-String -Path "D:\AI\MCP\server\py-calculator\.env" -Pattern "PHOENIX_ENDPOINT=http://localhost:8000/phoenix/v1/traces" -Quiet) {
    Write-Host "✓ py-calculator routes through Kong" -ForegroundColor Green
} else {
    Write-Host "⚠ py-calculator may be using direct Phoenix endpoint" -ForegroundColor Yellow
}

Write-Host "Checking go-calculator server .env... " -NoNewline
if (Select-String -Path "D:\AI\MCP\server\go-calculator\.env" -Pattern "PHOENIX_ENDPOINT=http://localhost:8000/phoenix/v1/traces" -Quiet) {
    Write-Host "✓ go-calculator routes through Kong" -ForegroundColor Green
} else {
    Write-Host "⚠ go-calculator may be using direct Phoenix endpoint" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "6. Testing Telemetry Flow" -ForegroundColor Yellow
Write-Host "--------------------------------------------"
# Phoenix OTLP endpoint - GET returns 200 (endpoint info page), POST accepts traces
Test-Reachable -Name "Phoenix OTLP endpoint via Kong" -Url "http://localhost:8000/phoenix/v1/traces"
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Verification Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. If Kong is not running:" -ForegroundColor White
Write-Host "   cd D:\AI\MCP\server\backend-gateway" -ForegroundColor Gray
Write-Host "   docker-compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "2. If backend services are not running, start them individually" -ForegroundColor White
Write-Host ""
Write-Host "3. Restart any services after updating .env files:" -ForegroundColor White
Write-Host "   - Restart py-calculator MCP server" -ForegroundColor Gray
Write-Host "   - Restart go-calculator MCP server" -ForegroundColor Gray
Write-Host "   - Restart frontend client" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Test the full application flow through Kong Gateway" -ForegroundColor White
Write-Host ""
