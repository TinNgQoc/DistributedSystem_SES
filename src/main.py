"""
Main program for SES Algorithm demonstration
Chương trình chính để khởi động và điều khiển process
"""

import sys
import os
import json
import time
import signal
from ses_process import SESProcess

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Thêm thư mục src vào path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_config(config_path="../config/config.json"):
    """
    Load configuration từ file
    
    Args:
        config_path: Đường dẫn đến file config
        
    Returns:
        Dictionary chứa configuration
    """
    config_file = os.path.join(os.path.dirname(__file__), config_path)
    with open(config_file, 'r') as f:
        return json.load(f)

def print_banner(process_id):
    """
    In banner khi khởi động process
    """
    print("\n" + "="*70)
    print(f"  SES ALGORITHM - CAUSAL ORDERING OF MESSAGES")
    print(f"  Process ID: {process_id}")
    print("="*70)
    print("\n  Thuật toán SES (Schiper-Eggli-Sandoz)")
    print("  - Đảm bảo causal ordering của messages trong hệ thống phân tán")
    print("  - Sử dụng V_P structure với (destination, timestamp) pairs")
    print("  - Buffering messages vi phạm causal order")
    print("\n  Phím tắt:")
    print("    's' - Hiển thị thống kê")
    print("    'v' - Hiển thị SES Vector")
    print("    'b' - Hiển thị trạng thái Buffer")
    print("    'q' - Thoát chương trình")
    print("="*70 + "\n")

def print_help():
    """
    In hướng dẫn sử dụng
    """
    print("\n" + "="*70)
    print("  HƯỚNG DẪN SỬ DỤNG")
    print("="*70)
    print("\n  Các lệnh có sẵn:")
    print("    's' hoặc 'stats'    - Hiển thị thống kê chi tiết")
    print("    'v' hoặc 'vc'       - Hiển thị SES Vector hiện tại")
    print("    'b' hoặc 'buffer'   - Hiển thị trạng thái Buffer")
    print("    'h' hoặc 'help'     - Hiển thị hướng dẫn này")
    print("    'q' hoặc 'quit'     - Thoát chương trình")
    print("="*70 + "\n")

def display_statistics(process):
    """
    Hiển thị thống kê của process
    """
    process.print_statistics()

def display_vector_clock(process):
    """
    Hiển thị SES Vector structure hiện tại
    """
    stats = process.get_statistics()
    print(f"\n{'='*60}")
    print(f"SES Vector của Process {process.process_id}")
    print(f"{'='*60}")
    print(f"Vector Time: {stats['vector_time']}")
    print(f"V_P Size: {stats['v_p_size']}")
    
    # Show details
    with process.vc_lock:
        print(f"\nChi tiết V_P:")
        if process.ses_vector.v_p:
            for dest, t_vec in process.ses_vector.v_p.items():
                print(f"  (P{dest}, {t_vec})")
        else:
            print("  (empty)")
    print(f"{'='*60}\n")

def display_buffer_status(process):
    """
    Hiển thị trạng thái buffer
    """
    stats = process.get_statistics()
    print(f"\n{'='*60}")
    print(f"Trạng thái Buffer của Process {process.process_id}")
    print(f"{'='*60}")
    print(f"Số messages đang trong buffer:    {stats['buffer_size']}")
    print(f"Tổng messages đã buffered:        {stats['total_buffered']}")
    print(f"Messages delivered từ buffer:     {stats['total_delivered_from_buffer']}")
    
    if stats['buffer_size'] > 0:
        print(f"\n⚠️  Hiện có {stats['buffer_size']} messages đang chờ trong buffer")
        print("   (Xem log file để biết chi tiết)")
    else:
        print("\n✓  Buffer trống - Tất cả messages đã được delivered")
    print(f"{'='*60}\n")

def handle_user_input(process):
    """
    Xử lý input từ người dùng
    
    Args:
        process: SESProcess instance
        
    Returns:
        True nếu tiếp tục, False nếu thoát
    """
    try:
        command = input("Nhập lệnh (h để xem hướng dẫn): ").strip().lower()
        
        if command in ['q', 'quit', 'exit']:
            return False
        elif command in ['s', 'stats', 'statistics']:
            display_statistics(process)
        elif command in ['v', 'vc', 'vector', 'clock']:
            display_vector_clock(process)
        elif command in ['b', 'buffer']:
            display_buffer_status(process)
        elif command in ['h', 'help']:
            print_help()
        elif command == '':
            pass  # Bỏ qua enter
        else:
            print(f"Lệnh không hợp lệ: '{command}'. Nhập 'h' để xem hướng dẫn.")
        
        return True
        
    except EOFError:
        return False
    except KeyboardInterrupt:
        return False

def main():
    """
    Hàm main của chương trình
    """
    # Kiểm tra arguments
    if len(sys.argv) < 2:
        print("Sử dụng: python main.py <process_id> [config_file]")
        print("Ví dụ: python main.py 0")
        print("       python main.py 1 config_custom.json")
        sys.exit(1)
    
    try:
        process_id = int(sys.argv[1])
    except ValueError:
        print("Error: process_id phải là số nguyên")
        sys.exit(1)
    
    # Config file (default hoặc custom)
    config_file = sys.argv[2] if len(sys.argv) > 2 else "config.json"
    config_path = f"../config/{config_file}"
    
    # Load configuration
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"Error loading config from {config_path}: {e}")
        sys.exit(1)
    
    # Kiểm tra process_id hợp lệ
    if process_id < 0 or process_id >= config['num_processes']:
        print(f"Error: process_id phải trong khoảng 0-{config['num_processes']-1}")
        sys.exit(1)
    
    # In banner
    print_banner(process_id)
    
    # Khởi tạo process
    print(f"Khởi tạo Process {process_id}...")
    process = SESProcess(process_id, config)
    
    # Biến để theo dõi trạng thái
    process_started = False
    
    def signal_handler(sig, frame):
        """Xử lý Ctrl+C"""
        print("\n\nĐang dừng process...")
        if process_started:
            process.stop()
        print("Đã dừng. Tạm biệt!")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Khởi động process
        print(f"Khởi động Process {process_id}...")
        process.start()
        process_started = True
        
        print(f"\n✓ Process {process_id} đã khởi động thành công!")
        print(f"  - Server đang lắng nghe trên {process.host}:{process.port}")
        print(f"  - Đang gửi {config['messages_per_process']} messages đến mỗi process khác")
        print(f"  - Log được ghi tại: logs/process_{process_id}.log")
        print("\nNhập 'h' để xem hướng dẫn sử dụng")
        print("Nhập 's' để xem thống kê")
        print("Nhập 'q' để thoát\n")
        
        # Vòng lặp xử lý input từ người dùng
        while True:
            if not handle_user_input(process):
                break
            time.sleep(0.1)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Dừng process
        print("\nĐang dừng process...")
        if process_started:
            # Hiển thị thống kê cuối cùng
            print("\nThống kê cuối cùng:")
            display_statistics(process)
            process.stop()
        
        # Đợi một chút để các threads dừng
        time.sleep(1)
        print("\nProcess đã dừng. Kiểm tra log file để xem chi tiết.")
        print(f"Log file: logs/process_{process_id}.log\n")

if __name__ == "__main__":
    main()
