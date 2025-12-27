# Endurance Test Runner Script
# Starts the server, runs the endurance test for 2+ hours, and cleans up

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item "$ScriptDir\..\..\..").FullName
$ResultsDir = "$ProjectRoot\tests\performance\results"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ServerProcess = $null

Write-Host "Endurance Test Runner"
Write-Host "====================="
Write-Host "Long-running stability test (2+ hours)"
Write-Host ""

# Function to cleanup on exit
function Cleanup {
    if ($null -ne $script:ServerProcess -and !$script:ServerProcess.HasExited) {
        Write-Host ""
        Write-Host "Stopping server (PID: $($script:ServerProcess.Id))..."
        Stop-Process -Id $script:ServerProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "Server stopped"
    }
}

# Register cleanup on script exit
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Cleanup }
trap { Cleanup; break }

try {
    # Build server if needed
    Set-Location $ProjectRoot
    if (-not (Test-Path "bin\calculator-server.exe")) {
        Write-Host "Building server..."
        New-Item -ItemType Directory -Path "bin" -Force | Out-Null
        go build -o bin/calculator-server.exe ./cmd/server
    }

    # Start server in background
    Write-Host "Starting server..."
    $serverPath = Join-Path $ProjectRoot "bin\calculator-server.exe"
    $script:ServerProcess = Start-Process -FilePath $serverPath -WorkingDirectory $ProjectRoot -PassThru -WindowStyle Hidden
    Write-Host "Server started (PID: $($script:ServerProcess.Id))"

    # Wait for server to be ready
    Write-Host "Waiting for server to be ready..."
    $MaxWait = 30
    $WaitCount = 0
    while ($WaitCount -lt $MaxWait) {
        try {
            # Use curl.exe (not PowerShell alias) for reliable HTTP checks
            $result = & curl.exe -s -o NUL -w "%{http_code}" "http://127.0.0.1:8200/health" 2>$null
            if ($result -eq "200") {
                Write-Host ""
                Write-Host "Server is ready" -ForegroundColor Green
                break
            }
        } catch {
            # Server not ready yet
        }
        Start-Sleep -Seconds 1
        $WaitCount++
        Write-Host -NoNewline "."
    }

    if ($WaitCount -eq $MaxWait) {
        Write-Host ""
        Write-Host "Server failed to start within $MaxWait seconds" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "Running endurance test..."
    Write-Host "WARNING: This test will run for over 2 hours!" -ForegroundColor Yellow
    Write-Host "Test profile:"
    Write-Host "  - Ramp up: 0 -> 50 VUs (5 min)"
    Write-Host "  - Sustain: 50 VUs (2 hours)"
    Write-Host "  - Ramp down: 50 -> 0 (5 min)"
    Write-Host ""
    Write-Host "Results will be saved to: $ResultsDir\endurance-$Timestamp.json"
    Write-Host ""
    Write-Host "Press Ctrl+C to cancel (you have 10 seconds)..."
    Start-Sleep -Seconds 10

    # Create results directory
    New-Item -ItemType Directory -Path $ResultsDir -Force | Out-Null

    # Run k6 test
    $k6Result = k6 run --out "json=$ResultsDir\endurance-$Timestamp.json" "$ProjectRoot\tests\performance\k6\scenarios\endurance-test.js"

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Endurance test completed successfully" -ForegroundColor Green
        Write-Host ""
        Write-Host "Results saved to: $ResultsDir\endurance-$Timestamp.json"
        Write-Host "Review memory trends to detect leaks"
    } else {
        Write-Host ""
        Write-Host "Endurance test failed" -ForegroundColor Red
        exit 1
    }
} finally {
    Cleanup
}
