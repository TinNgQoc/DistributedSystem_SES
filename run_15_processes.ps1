#!/usr/bin/env powershell
# Simple demo runner for 15 processes
# Each process sends 150 messages to 14 other processes

param(
    [int]$ProcessCount = 15,
    [int]$Delay = 2
)

Write-Host "🚀 Starting SES Distributed System Demo" -ForegroundColor Green
Write-Host "📊 Configuration:" -ForegroundColor Cyan
Write-Host "   - Process Count: $ProcessCount" -ForegroundColor White
Write-Host "   - Messages per process: 150 (total ~2250 per process)" -ForegroundColor White
Write-Host "   - Total system messages: ~33,750" -ForegroundColor White
Write-Host ""

# Create logs directory if not exists
$LogDir = "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    Write-Host "📁 Created log directory: $LogDir" -ForegroundColor Green
}

Write-Host "🔄 Starting processes..." -ForegroundColor Yellow

# Start processes in background
$processes = @()
for ($i = 0; $i -lt $ProcessCount; $i++) {
    Write-Host "   Starting Process $i..." -ForegroundColor Gray
    
    $logFile = "$LogDir\pid_$i.txt"
    
    # Start process in background
    $proc = Start-Process -FilePath "python" -ArgumentList @("run_node.py", $i) `
        -RedirectStandardOutput $logFile `
        -RedirectStandardError "$LogDir\pid_$i.err" `
        -NoNewWindow -PassThru
    
    $processes += $proc
    Start-Sleep -Milliseconds 500  # Brief delay between starts
}

Write-Host ""
Write-Host "✅ All $ProcessCount processes started!" -ForegroundColor Green
Write-Host "📝 Logs are being written to: $LogDir\" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔍 Real-time monitoring:" -ForegroundColor Yellow
Write-Host "   - Watch logs: Get-Content $LogDir\pid_0.txt -Wait" -ForegroundColor Gray
Write-Host "   - Check all processes: Get-Process python" -ForegroundColor Gray
Write-Host ""

Write-Host "⏱️  Demo running... Let processes communicate for 30 seconds" -ForegroundColor Cyan

# Let demo run for 30 seconds
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "🛑 Stopping demo..." -ForegroundColor Yellow

# Stop all processes
foreach ($proc in $processes) {
    if (-not $proc.HasExited) {
        Write-Host "   Stopping Process $($proc.Id)..." -ForegroundColor Gray
        try {
            $proc.Kill()
            $proc.WaitForExit(5000)  # Wait up to 5 seconds
        }
        catch {
            Write-Warning "Failed to stop process $($proc.Id): $_"
        }
    }
}

Write-Host ""
Write-Host "📊 Demo completed! Check results:" -ForegroundColor Green
Write-Host "   - Log files in: $LogDir\" -ForegroundColor Cyan
Write-Host "   - Message counts: Select-String 'Message.*delivered' $LogDir\*.txt | Measure-Object" -ForegroundColor Gray
Write-Host "   - Error analysis: Select-String 'ERROR\\|Exception' $LogDir\*.txt" -ForegroundColor Gray

# Show quick stats
Write-Host ""
Write-Host "📈 Quick Statistics:" -ForegroundColor Cyan
$logFiles = Get-ChildItem "$LogDir\pid_*.txt" -ErrorAction SilentlyContinue
if ($logFiles) {
    $totalLines = ($logFiles | Get-Content | Measure-Object -Line).Lines
    $deliveredMessages = (Select-String "delivered" $logFiles.FullName | Measure-Object).Count
    $bufferedMessages = (Select-String "buffered" $logFiles.FullName | Measure-Object).Count
    
    Write-Host "   - Total log entries: $totalLines" -ForegroundColor White
    Write-Host "   - Messages delivered: $deliveredMessages" -ForegroundColor Green
    Write-Host "   - Messages buffered: $bufferedMessages" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 SES Demo Complete!" -ForegroundColor Green