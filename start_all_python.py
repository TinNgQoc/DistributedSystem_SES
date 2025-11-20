"""
Script Python để khởi động tất cả 15 processes
Dễ dàng hơn và ổn định hơn PowerShell script
"""

import subprocess
import sys
import os
import time

def main():
    print("="*70)
    print("  SES ALGORITHM - Starting All 15 Processes")
    print("="*70)
    print()
    
    # Kiểm tra Python
    python_version = sys.version
    print(f"Python version: {python_version}")
    print()
    
    # Tạo thư mục logs nếu chưa có
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Xóa log files cũ
    for i in range(15):
        log_file = os.path.join(logs_dir, f"process_{i}.log")
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
            except:
                pass
    print("Đã xóa log files cũ\n")
    
    print("Đang khởi động 15 processes...")
    print("Nhấn Ctrl+C để dừng tất cả processes\n")
    
    # Danh sách processes
    processes = []
    src_dir = os.path.join(os.path.dirname(__file__), "src")
    
    # Khởi động từng process
    for i in range(15):
        try:
            # Sử dụng CREATE_NEW_CONSOLE trên Windows để mở cửa sổ mới
            if sys.platform == 'win32':
                CREATE_NEW_CONSOLE = 0x00000010
                proc = subprocess.Popen(
                    [sys.executable, "main.py", str(i)],
                    cwd=src_dir,
                    creationflags=CREATE_NEW_CONSOLE
                )
            else:
                # Linux/Mac
                proc = subprocess.Popen(
                    [sys.executable, "main.py", str(i)],
                    cwd=src_dir
                )
            
            processes.append(proc)
            print(f"✓ Process {i} khởi động (PID: {proc.pid})")
            time.sleep(0.3)  # Đợi một chút giữa các process
            
        except Exception as e:
            print(f"✗ Lỗi khởi động Process {i}: {e}")
    
    print()
    print("="*70)
    print(f"  ✓ Đã khởi động {len(processes)}/15 processes thành công!")
    print("="*70)
    print()
    print("Mỗi process đang chạy trong cửa sổ riêng")
    print(f"Log files: {logs_dir}")
    print()
    print("Nhấn Ctrl+C để dừng tất cả processes...")
    print()
    
    try:
        # Đợi người dùng nhấn Ctrl+C
        while True:
            time.sleep(1)
            # Kiểm tra xem có process nào còn chạy không
            alive = sum(1 for p in processes if p.poll() is None)
            if alive == 0:
                print("\nTất cả processes đã dừng.")
                break
                
    except KeyboardInterrupt:
        print("\n\nĐang dừng tất cả processes...")
        
        # Dừng tất cả processes
        for i, proc in enumerate(processes):
            if proc.poll() is None:  # Nếu process còn chạy
                try:
                    proc.terminate()
                    print(f"  Dừng Process {i}")
                except:
                    pass
        
        # Đợi processes dừng
        time.sleep(2)
        
        # Force kill nếu cần
        for proc in processes:
            if proc.poll() is None:
                try:
                    proc.kill()
                except:
                    pass
        
        print("\n✓ Tất cả processes đã dừng!")
        print()

if __name__ == "__main__":
    main()
