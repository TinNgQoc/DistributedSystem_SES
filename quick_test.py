"""
Quick test - Chạy Process 0 với config test
"""

import sys
import os

# Thêm thư mục src vào path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import json
import time
import signal
from ses_process import SESProcess

def main():
    print("\n" + "="*70)
    print("  QUICK TEST - Process 0")
    print("="*70 + "\n")
    
    # Load config test
    config_file = os.path.join(os.path.dirname(__file__), "config", "config.json")
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Tạo process 0
    process = SESProcess(0, config)
    
    def signal_handler(sig, frame):
        print("\n\nDừng process...")
        process.stop()
        process.print_statistics()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Khởi động
    print("Khởi động Process 0...")
    process.start()
    
    print(f"✓ Process 0 đang chạy trên {process.host}:{process.port}")
    print(f"✓ Đang gửi {config['messages_per_process']} messages tới mỗi process")
    print("\nĐể xem thống kê, đợi 10 giây rồi nhấn Ctrl+C\n")
    
    # Chờ một lúc
    try:
        time.sleep(30)  # Chạy 30 giây
        print("\n" + "="*70)
        print("  THỐNG KÊ SAU 30 GIÂY")
        print("="*70)
        process.print_statistics()
        
        print("\nNhấn Ctrl+C để dừng hoặc đợi thêm...")
        while True:
            time.sleep(5)
            process.print_statistics()
            
    except KeyboardInterrupt:
        print("\n\nDừng process...")
        process.stop()
        process.print_statistics()

if __name__ == "__main__":
    main()
