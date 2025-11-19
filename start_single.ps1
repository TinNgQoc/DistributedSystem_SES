# Script để chạy một process đơn lẻ
# Sử dụng: .\start_single.ps1 <process_id>
# Ví dụ: .\start_single.ps1 0

param(
    [Parameter(Mandatory=$true)]
    [int]$ProcessId
)

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$srcPath = Join-Path $scriptPath "src"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SES ALGORITHM - Process $ProcessId" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Kiểm tra process_id hợp lệ
if ($ProcessId -lt 0 -or $ProcessId -gt 14) {
    Write-Host "Error: ProcessId phải trong khoảng 0-14" -ForegroundColor Red
    exit 1
}

# Kiểm tra Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python không được tìm thấy." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Khởi động Process $ProcessId..." -ForegroundColor Green
Write-Host ""

# Chuyển đến thư mục src và chạy
Set-Location $srcPath
python main.py $ProcessId
