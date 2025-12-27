# Run Quick Performance Test for MCP Calculator Server
# Windows PowerShell script
# Use this for quick smoke tests or CI/CD pipelines

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MCP Calculator - Quick Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Configuration
$SERVER_URL = if ($env:SERVER_URL) { $env:SERVER_URL } else { "http://127.0.0.1:8100" }
$DURATION = if ($env:TEST_DURATION) { $env:TEST_DURATION } else { "30s" }
$VUS = if ($env:TEST_VUS) { $env:TEST_VUS } else { "5" }

# Check if k6 is installed
if (-not (Get-Command k6 -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: k6 is not installed" -ForegroundColor Red
    Write-Host "Install k6 using: choco install k6" -ForegroundColor Yellow
    exit 1
}

# Check if server is running
Write-Host "Checking server availability at $SERVER_URL..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$SERVER_URL/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ Server is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Server is not responding at $SERVER_URL" -ForegroundColor Red
    Write-Host "Start the server with: uv run python -m calculator.server" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Starting quick performance test..." -ForegroundColor Yellow
Write-Host "Duration: $DURATION" -ForegroundColor White
Write-Host "VUs: $VUS" -ForegroundColor White
Write-Host ""

# Run the test
$env:SERVER_URL = $SERVER_URL
k6 run --duration $DURATION --vus $VUS tests/performance/k6/scenarios/load-test.js

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Quick Test PASSED" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Quick Test FAILED" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}
