# Load Test Runner Script
# Starts the server, runs the load test, and cleans up

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item "$ScriptDir\..\..\..").FullName
$ResultsDir = "$ProjectRoot\tests\performance\results"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ServerProcess = $null

Write-Host "Load Test Runner"
Write-Host "================"
Write-Host "Project root: $ProjectRoot"
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
    Write-Host "Running load test..."
    Write-Host "Results will be saved to: $ResultsDir\load-$Timestamp.json"
    Write-Host ""

    # Create results directory
    New-Item -ItemType Directory -Path $ResultsDir -Force | Out-Null

    # Run k6 test
    $k6Result = k6 run --out "json=$ResultsDir\load-$Timestamp.json" "$ProjectRoot\tests\performance\k6\scenarios\load-test.js"

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Load test completed successfully" -ForegroundColor Green
        Write-Host ""
        Write-Host "Results saved to: $ResultsDir\load-$Timestamp.json"
    } else {
        Write-Host ""
        Write-Host "Load test failed" -ForegroundColor Red
        exit 1
    }
} finally {
    Cleanup
}
