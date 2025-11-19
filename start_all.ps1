# Script để chạy tất cả 15 processes cùng lúc
# Mỗi process sẽ chạy trong một PowerShell window riêng

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$srcPath = Join-Path $scriptPath "src"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SES ALGORITHM - Starting All Processes" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Kiểm tra xem Python có được cài đặt không
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python không được tìm thấy. Vui lòng cài đặt Python." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Đang khởi động 15 processes..." -ForegroundColor Yellow
Write-Host ""

# Tạo thư mục logs nếu chưa tồn tại
$logsPath = Join-Path $scriptPath "logs"
if (-not (Test-Path $logsPath)) {
    New-Item -ItemType Directory -Path $logsPath | Out-Null
}

# Xóa log files cũ
Get-ChildItem -Path $logsPath -Filter "*.log" | Remove-Item -Force
Write-Host "Đã xóa log files cũ" -ForegroundColor Gray

# Array để lưu các process
$processes = @()

# Khởi động 15 processes
for ($i = 0; $i -lt 15; $i++) {
    $processTitle = "SES Process $i"
    
    Write-Host "Khởi động Process $i..." -ForegroundColor Green
    
    # Khởi động process trong PowerShell window mới
    $proc = Start-Process -FilePath "powershell.exe" `
        -ArgumentList "-NoExit", "-Command", "cd '$srcPath'; python main.py $i; Read-Host 'Press Enter to close'" `
        -PassThru `
        -WindowStyle Normal
    
    $processes += $proc
    
    # Đợi lâu hơn giữa các process để server có thời gian khởi động
    Start-Sleep -Milliseconds 800
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Tất cả 15 processes đã được khởi động!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Mỗi process đang chạy trong một cửa sổ riêng" -ForegroundColor Yellow
Write-Host "Log files được lưu tại: $logsPath" -ForegroundColor Yellow
Write-Host ""
Write-Host "Để dừng tất cả processes:" -ForegroundColor Cyan
Write-Host "  1. Đóng từng cửa sổ process" -ForegroundColor White
Write-Host "  2. Hoặc nhấn bất kỳ phím nào ở đây để dừng tất cả" -ForegroundColor White
Write-Host ""

# Chờ người dùng nhấn phím để dừng
Read-Host "Nhấn Enter để dừng tất cả processes"

Write-Host ""
Write-Host "Đang dừng tất cả processes..." -ForegroundColor Yellow

# Dừng tất cả processes
foreach ($proc in $processes) {
    if (-not $proc.HasExited) {
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        } catch {
            # Ignore errors
        }
    }
}

Write-Host "Tất cả processes đã dừng!" -ForegroundColor Green
Write-Host ""
