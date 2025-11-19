"""
Script demo đầy đủ với 15 processes
Chạy đủ lâu để tạo log và xem kết quả
"""

import subprocess
import sys
import os
import time

def main():
    print("="*70)
    print("  SES ALGORITHM DEMO - 15 Processes")
    print("="*70)
    print()
    
    # Tạo thư mục logs
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        print(f"✓ Đã tạo thư mục logs")
    
    # Xóa log files cũ
    deleted = 0
    for i in range(15):
        log_file = os.path.join(logs_dir, f"process_{i}.log")
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
                deleted += 1
            except:
                pass
    if deleted > 0:
        print(f"✓ Đã xóa {deleted} log files cũ")
    print()
    
    print("KHỞI ĐỘNG 15 PROCESSES...")
    print("=" * 70)
    
    processes = []
    src_dir = os.path.join(os.path.dirname(__file__), "src")
    
    # Khởi động từng process
    for i in range(15):
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
            
            processes.append((i, proc))
            print(f"  [P{i:2d}] Started (PID: {proc.pid})")
            time.sleep(0.4)  # Đợi giữa các process
            
        except Exception as e:
            print(f"  [P{i:2d}] ERROR: {e}")
    
    print("=" * 70)
    print()
    print(f"✓ THÀNH CÔNG! Đã khởi động {len(processes)}/15 processes")
    print()
    print("Mỗi process đang:")
    print("  - Gửi 150 messages đến mỗi process khác (2100 messages/process)")
    print("  - Message rate: 10-100 messages/phút (ngẫu nhiên)")
    print("  - Sử dụng Vector Clock để đảm bảo causal ordering")
    print("  - Buffer messages vi phạm causal order")
    print()
    print(f"📁 Log files: {logs_dir}")
    print()
    print("Chương trình sẽ chạy trong 60 giây...")
    print("Nhấn Ctrl+C bất kỳ lúc nào để dừng")
    print()
    
    start_time = time.time()
    countdown = 60
    
    try:
        while countdown > 0:
            # Kiểm tra processes còn sống
            alive = sum(1 for _, p in processes if p.poll() is None)
            elapsed = int(time.time() - start_time)
            remaining = max(0, 60 - elapsed)
            
            print(f"\r⏱️  Running: {elapsed}s | Remaining: {remaining}s | Alive: {alive}/15 processes", end="", flush=True)
            time.sleep(1)
            countdown -= 1
            
            if alive == 0:
                print("\n\n⚠️  Tất cả processes đã dừng.")
                break
        
        print("\n")
        print("=" * 70)
        print("  ✓ HOÀN THÀNH - Đang thu thập thống kê...")
        print("=" * 70)
        print()
        
        # Hiển thị thống kê từ log files
        print("THỐNG KÊ TỪ LOG FILES:")
        print("-" * 70)
        for i in range(15):
            log_file = os.path.join(logs_dir, f"process_{i}.log")
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        sent = sum(1 for line in lines if 'SEND:' in line)
                        received = sum(1 for line in lines if 'RECEIVE:' in line)
                        buffered = sum(1 for line in lines if 'BUFFERED:' in line)
                        delivered = sum(1 for line in lines if 'DELIVERED' in line)
                        
                        print(f"  P{i:2d}: Sent={sent:4d} | Recv={received:4d} | Delivered={delivered:4d} | Buffered={buffered:4d}")
                except Exception as e:
                    print(f"  P{i:2d}: Error reading log - {e}")
            else:
                print(f"  P{i:2d}: No log file")
        
        print("-" * 70)
        print()
        print("📝 Xem chi tiết trong log files:")
        print(f"   {logs_dir}\\process_0.log")
        print(f"   {logs_dir}\\process_1.log")
        print("   ...")
        print()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Đã nhận Ctrl+C - Đang dừng processes...")
        print()
    
    # Dừng tất cả processes
    print("Đang dừng processes...")
    for i, proc in processes:
        if proc.poll() is None:
            try:
                proc.terminate()
                print(f"  Stopped P{i}")
            except:
                pass
    
    # Đợi một chút
    time.sleep(2)
    
    # Force kill nếu cần
    for _, proc in processes:
        if proc.poll() is None:
            try:
                proc.kill()
            except:
                pass
    
    print()
    print("=" * 70)
    print("  ✓ DEMO KẾT THÚC")
    print("=" * 70)
    print()
    print("Để xem log của một process cụ thể:")
    print("  python -c \"import sys; print(open('logs/process_0.log').read())\"")
    print()
    print("Hoặc sử dụng:")
    print("  .\\view_logs.ps1 0")
    print()

if __name__ == "__main__":
    main()
