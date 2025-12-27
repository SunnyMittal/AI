# Run Stress Test for MCP Calculator Server
# Windows PowerShell script

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MCP Calculator - Stress Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Configuration
$SERVER_URL = if ($env:SERVER_URL) { $env:SERVER_URL } else { "http://127.0.0.1:8100" }
$RESULTS_DIR = "tests/performance/results"
$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$OUTPUT_FILE = "$RESULTS_DIR/stress-test-$TIMESTAMP.json"

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
Write-Host "WARNING: This test will push the server to its limits" -ForegroundColor Red
Write-Host "Duration: ~20 minutes" -ForegroundColor White
Write-Host "Max VUs: 800 (progressive ramp)" -ForegroundColor White
Write-Host "Results: $OUTPUT_FILE" -ForegroundColor White
Write-Host ""

# Run the test
$env:SERVER_URL = $SERVER_URL
k6 run --out "json=$OUTPUT_FILE" tests/performance/k6/scenarios/stress-test.js

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Stress Test Complete" -ForegroundColor Cyan
Write-Host "Review metrics to identify breaking points" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
