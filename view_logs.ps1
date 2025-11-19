# Script để view logs của một process cụ thể
# Sử dụng: .\view_logs.ps1 <process_id>
# Ví dụ: .\view_logs.ps1 0

param(
    [Parameter(Mandatory=$true)]
    [int]$ProcessId
)

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$logFile = Join-Path $scriptPath "logs\process_$ProcessId.log"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Log của Process $ProcessId" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $logFile)) {
    Write-Host "Log file không tồn tại: $logFile" -ForegroundColor Red
    Write-Host "Process $ProcessId có thể chưa được chạy." -ForegroundColor Yellow
    exit 1
}

Write-Host "Đang hiển thị log file: $logFile" -ForegroundColor Green
Write-Host "Nhấn Ctrl+C để thoát" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Hiển thị log file với màu sắc
Get-Content $logFile -Tail 50 -Wait | ForEach-Object {
    if ($_ -match "ERROR") {
        Write-Host $_ -ForegroundColor Red
    } elseif ($_ -match "WARNING|BUFFERED") {
        Write-Host $_ -ForegroundColor Yellow
    } elseif ($_ -match "DELIVERED") {
        Write-Host $_ -ForegroundColor Green
    } elseif ($_ -match "SEND") {
        Write-Host $_ -ForegroundColor Cyan
    } elseif ($_ -match "RECEIVE") {
        Write-Host $_ -ForegroundColor Magenta
    } else {
        Write-Host $_
    }
}
