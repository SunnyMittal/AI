# Run Endurance Test for MCP Calculator Server
# Windows PowerShell script

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MCP Calculator - Endurance Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Configuration
$SERVER_URL = if ($env:SERVER_URL) { $env:SERVER_URL } else { "http://127.0.0.1:8000" }
$RESULTS_DIR = "tests/performance/results"
$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$OUTPUT_FILE = "$RESULTS_DIR/endurance-test-$TIMESTAMP.json"

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

# Create results directory
if (-not (Test-Path $RESULTS_DIR)) {
    New-Item -ItemType Directory -Path $RESULTS_DIR -Force | Out-Null
}

Write-Host ""
Write-Host "WARNING: This is a long-running test!" -ForegroundColor Red
Write-Host "Duration: ~2 hours 10 minutes" -ForegroundColor White
Write-Host "VUs: 50 (constant)" -ForegroundColor White
Write-Host "Purpose: Detect memory leaks and degradation" -ForegroundColor White
Write-Host "Results: $OUTPUT_FILE" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to cancel within 10 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Run the test
$env:SERVER_URL = $SERVER_URL
k6 run --out "json=$OUTPUT_FILE" tests/performance/k6/scenarios/endurance-test.js

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Endurance Test Complete" -ForegroundColor Green
Write-Host "Check memory metrics for leaks" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
