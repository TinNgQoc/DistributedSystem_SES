"""
Script test với 3 processes để dễ kiểm tra
"""

import subprocess
import sys
import os
import time

def main():
    print("="*70)
    print("  SES ALGORITHM - Test với 3 Processes")
    print("="*70)
    print()
    
    # Tạo thư mục logs
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
    
    print("Đang khởi động 3 processes (0, 1, 2)...")
    print()
    
    processes = []
    src_dir = os.path.join(os.path.dirname(__file__), "src")
    
    # Khởi động 3 processes
    for i in range(3):
        try:
            if sys.platform == 'win32':
                CREATE_NEW_CONSOLE = 0x00000010
                proc = subprocess.Popen(
                    [sys.executable, "main.py", str(i)],
                    cwd=src_dir,
                    creationflags=CREATE_NEW_CONSOLE
                )
            else:
                proc = subprocess.Popen(
                    [sys.executable, "main.py", str(i)],
                    cwd=src_dir
                )
            
            processes.append(proc)
            print(f"✓ Process {i} started (PID: {proc.pid})")
            time.sleep(1)
            
        except Exception as e:
            print(f"✗ Error starting Process {i}: {e}")
    
    print()
    print("="*70)
    print(f"  ✓ Started {len(processes)}/3 processes")
    print("="*70)
    print()
    print("Mỗi process đang gửi messages cho nhau...")
    print("Xem log files trong thư mục: logs/")
    print()
    print("Nhấn Ctrl+C để dừng...")
    print()
    
    try:
        while True:
            time.sleep(1)
            alive = sum(1 for p in processes if p.poll() is None)
            if alive == 0:
                print("\nTất cả processes đã dừng.")
                break
                
    except KeyboardInterrupt:
        print("\n\nĐang dừng processes...")
        
        for i, proc in enumerate(processes):
            if proc.poll() is None:
                try:
                    proc.terminate()
                    print(f"  Stopped Process {i}")
                except:
                    pass
        
        time.sleep(2)
        
        for proc in processes:
            if proc.poll() is None:
                try:
                    proc.kill()
                except:
                    pass
        
        print("\n✓ Đã dừng tất cả processes!")

if __name__ == "__main__":
    main()
