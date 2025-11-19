"""
Demo nhỏ với 3 processes để dễ quan sát buffer và causal ordering
"""

import subprocess
import sys
import os
import time
import json

def main():
    print("="*70)
    print("  DEMO NHỎ - 3 Processes để quan sát Buffering & Causal Ordering")
    print("="*70)
    print()
    
    # Thay đổi config tạm thời
    config_file = os.path.join(os.path.dirname(__file__), "config", "config.json")
    config_test = os.path.join(os.path.dirname(__file__), "config", "config_test.json")
    
    # Backup config cũ
    with open(config_file, 'r') as f:
        original_config = f.read()
    
    try:
        # Copy test config
        with open(config_test, 'r') as f:
            test_config = f.read()
        with open(config_file, 'w') as f:
            f.write(test_config)
        
        print("✓ Đã cấu hình: 3 processes, 30 messages/process, rate 60-120 msg/min")
        print()
        
        # Xóa logs cũ
        logs_dir = os.path.join(os.path.dirname(__file__), "logs")
        for i in range(15):
            log_file = os.path.join(logs_dir, f"process_{i}.log")
            if os.path.exists(log_file):
                try:
                    os.remove(log_file)
                except:
                    pass
        
        print("Đang khởi động 3 processes...")
        print()
        
        processes = []
        src_dir = os.path.join(os.path.dirname(__file__), "src")
        
        # Khởi động 3 processes
        for i in range(3):
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
            
            processes.append((i, proc))
            print(f"  [P{i}] Started (PID: {proc.pid})")
            time.sleep(0.5)
        
        print()
        print("="*70)
        print("  ✓ 3 processes đang chạy")
        print("="*70)
        print()
        print("Chạy trong 30 giây để quan sát buffering...")
        print()
        
        # Chạy 30 giây
        for i in range(30):
            alive = sum(1 for _, p in processes if p.poll() is None)
            print(f"\r⏱️  {i+1}/30 giây | Processes: {alive}/3", end="", flush=True)
            time.sleep(1)
        
        print("\n")
        print("="*70)
        print("  ✓ HOÀN THÀNH - Đang dừng processes...")
        print("="*70)
        print()
        
        # Dừng processes
        for i, proc in processes:
            if proc.poll() is None:
                try:
                    proc.terminate()
                    print(f"  Stopped P{i}")
                except:
                    pass
        
        time.sleep(2)
        
        # Hiển thị kết quả
        print()
        print("="*70)
        print("  📊 KẾT QUẢ")
        print("="*70)
        print()
        
        for i in range(3):
            log_file = os.path.join(logs_dir, f"process_{i}.log")
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    import re
                    sent = len(re.findall(r'INFO - SEND:', content))
                    buffered = len(re.findall(r'WARNING - BUFFERED:', content))
                    delivered = len(re.findall(r'INFO - DELIVERED', content))
                    buffer_release = len(re.findall(r'INFO - BUFFER_RELEASE:', content))
                    
                    print(f"Process {i}:")
                    print(f"  Sent: {sent}, Delivered: {delivered}, Buffered: {buffered}")
                    print(f"  Buffer Releases: {buffer_release}")
                    print()
        
        print("="*70)
        print()
        print("📝 Xem chi tiết trong log files:")
        print()
        print("  Xem buffering:")
        print(f"  Get-Content logs\\process_0.log | Select-String 'BUFFERED' | Select -First 10")
        print()
        print("  Xem buffer release (message Y trigger message X):")
        print(f"  Get-Content logs\\process_0.log | Select-String 'BUFFER_RELEASE'")
        print()
        print("  Xem delivery với Vector Clock changes:")
        print(f"  Get-Content logs\\process_0.log | Select-String 'DELIVERED'")
        print()
        
    finally:
        # Restore config
        with open(config_file, 'w') as f:
            f.write(original_config)
        print("✓ Đã khôi phục config gốc (15 processes)")
        print()

if __name__ == "__main__":
    main()
