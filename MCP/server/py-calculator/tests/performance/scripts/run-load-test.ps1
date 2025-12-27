# Run Load Test for MCP Calculator Server
# Windows PowerShell script

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MCP Calculator - Load Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Configuration
$SERVER_URL = if ($env:SERVER_URL) { $env:SERVER_URL } else { "http://127.0.0.1:8100" }
$RESULTS_DIR = "tests/performance/results"
$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$OUTPUT_FILE = "$RESULTS_DIR/load-test-$TIMESTAMP.json"

# Check if k6 is installed
if (-not (Get-Command k6 -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: k6 is not installed" -ForegroundColor Red
    Write-Host "Install k6 using: choco install k6" -ForegroundColor Yellow
    Write-Host "Or: winget install k6" -ForegroundColor Yellow
    exit 1
}

# Check if server is running
Write-Host "Checking server availability at $SERVER_URL..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$SERVER_URL/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -ne 200) {
        throw "Server health check failed"
    }
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
Write-Host "Starting load test..." -ForegroundColor Yellow
Write-Host "Duration: ~14 minutes" -ForegroundColor White
Write-Host "Max VUs: 100" -ForegroundColor White
Write-Host "Results: $OUTPUT_FILE" -ForegroundColor White
Write-Host ""

# Run the test
$env:SERVER_URL = $SERVER_URL
k6 run --out "json=$OUTPUT_FILE" tests/performance/k6/scenarios/load-test.js

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Load Test PASSED" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Load Test FAILED" -ForegroundColor Red
    Write-Host "Check output above for details" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}
